"""Roda o verificador sobre os CEVs de referência e compara cada achado com as
marcas VERMELHAS da verificadora na mesma região (anotações e comentários de
rodadas anteriores achatados no conteúdo).

Uso:  python -X utf8 ferramentas/validar_referencias.py [pasta_cevs] [--lote 1] [--sem-pdf]
Saída: saida_teste/validacao.csv e saida_teste/validacao_resumo.txt

"Próximo de uma marca vermelha" NÃO prova acerto (a marca pode ser sobre outra
coisa) e "sem marca" NÃO prova falso positivo (a verificadora pode não ter
comentado). O CSV traz o texto do comentário humano mais próximo para conferência.
"""
from __future__ import annotations

import argparse
import csv
import glob
import os
import sys
from collections import Counter, defaultdict

import fitz

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from verificador.anotador import anotar, numerar, tag  # noqa: E402
from verificador.cli import caminho_saida  # noqa: E402
from verificador.config import Config  # noqa: E402
from verificador.extracao import _cor_proxima, extrair_documento  # noqa: E402
from verificador.regras import executar  # noqa: E402
from verificador import ld as ld_mod  # noqa: E402
from verificador.carimbo import reconhecer  # noqa: E402

VERMELHOS = ["ff0000", "ef5350", "d32f2f"]
AUTOR_AUTO = "Verificador Automático"


def _vermelho_rgb(c) -> bool:
    if not c:
        return False
    r, g, b = (int(round(x * 255)) for x in c[:3])
    return any(_cor_proxima((r << 16) | (g << 8) | b, v, 30) for v in VERMELHOS)


def marcas_humanas(caminho: str, cfg: Config):
    """{pagina: [(rect_exibicao, tipo, texto)]}"""
    out = defaultdict(list)
    with fitz.open(caminho) as doc:
        for page in doc:
            m = page.rotation_matrix
            tm = page.transformation_matrix
            for a in page.annots() or []:
                autor = a.info.get("title", "")
                if autor in ("AutoCAD SHX Text", AUTOR_AUTO):
                    continue
                tipo = a.type[1]
                cor = a.colors.get("stroke") or a.colors.get("fill")
                da = doc.xref_get_key(a.xref, "DA")[1]
                vermelho = _vermelho_rgb(cor) if tipo != "FreeText" else (
                    da.startswith("1 0 0 rg") or da.startswith(".937 .325 .314 rg") or da.startswith("0.937"))
                if not vermelho:
                    continue
                r = fitz.Rect(a.rect) * m
                texto = (a.info.get("content") or "").replace("\r", " ").replace("\n", " ")
                out[page.number].append((r, tipo, texto))
                cl = doc.xref_get_key(a.xref, "CL")
                if tipo == "FreeText" and cl[0] == "array":
                    nums = [float(x) for x in cl[1].strip("[]").split()]
                    if len(nums) >= 2:
                        p = fitz.Point(nums[0], nums[1]) * tm * m
                        out[page.number].append((fitz.Rect(p.x - 3, p.y - 3, p.x + 3, p.y + 3), "Ponta", texto))
            # comentários de rodadas anteriores achatados no conteúdo
            for b in page.get_text("dict")["blocks"]:
                if b["type"]:
                    continue
                for ln in b["lines"]:
                    sp = [s for s in ln["spans"] if s["text"].strip()]
                    if sp and any(_cor_proxima(sp[0]["color"], v, 12) for v in VERMELHOS):
                        out[page.number].append((fitz.Rect(ln["bbox"]) * m, "Achatado",
                                                 " ".join(s["text"] for s in sp)))
    return out


def _dist(a: fitz.Rect, b: fitz.Rect) -> float:
    dx = max(b.x0 - a.x1, a.x0 - b.x1, 0)
    dy = max(b.y0 - a.y1, a.y0 - b.y1, 0)
    return (dx * dx + dy * dy) ** 0.5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pasta", nargs="?", default="referencias/CEV-Referencias/VerificadorProjetos_CEV-Referencias")
    ap.add_argument("--lote", type=int, default=1)
    ap.add_argument("--sem-pdf", action="store_true", help="não gravar os PDFs anotados")
    ap.add_argument("--raio-mm", type=float, default=15)
    args = ap.parse_args()
    cfg = Config(lote_teste=args.lote)
    pt = cfg.mm_para_pt(1)
    raio = args.raio_mm * pt
    os.makedirs("saida_teste", exist_ok=True)
    linhas = []
    lds = {}
    por_regra = defaultdict(Counter)
    for f in sorted(glob.glob(os.path.join(args.pasta, "*.pdf"))):
        nome = os.path.basename(f)
        doc = extrair_documento(f, cfg)
        car = reconhecer(doc.paginas[0], cfg) if doc.paginas else None
        op = ld_mod.operacao_de(*(c.valor for c in (car.campos.values() if car else [])))
        cam = ld_mod.localizar(f, cfg, None, op) if op else None
        if cam and cam not in lds:
            lds[cam] = ld_mod.ler(cam, cfg)
        achados = numerar(executar(doc, cfg, None, lds.get(cam)))
        if not args.sem_pdf:
            anotar(f, caminho_saida(f, cfg, "saida_teste"), achados, cfg,
                   {p.indice: [l.bbox for l in p.linhas] for p in doc.paginas})
        marcas = marcas_humanas(f, cfg)
        for a in achados:
            cands = sorted(((_dist(a.alvo, r), tipo, txt) for r, tipo, txt in marcas.get(a.pagina, [])), key=lambda x: x[0])
            perto = [c for c in cands if c[0] <= raio]
            com_texto = next((c for c in cands if c[2].strip()), None)
            casou = bool(perto)
            por_regra[a.regra]["achados"] += 1
            por_regra[a.regra]["com_marca_vermelha_ate_%dmm" % args.raio_mm] += casou
            por_regra[a.regra]["docs"] += 0
            linhas.append({
                "arquivo": nome, "folha": a.pagina + 1, "indice": tag(cfg, a), "regra": a.regra,
                "severidade": a.severidade, "achado": a.texto,
                "marca_vermelha_ate_raio": "SIM" if casou else "não",
                "dist_marca_mm": round(cands[0][0] / pt) if cands else "",
                "tipo_marca": cands[0][1] if cands else "",
                "comentario_humano_mais_proximo": (com_texto[2][:200] if com_texto else ""),
                "dist_comentario_mm": (round(com_texto[0] / pt) if com_texto else ""),
            })
        print(f"{nome}: {len(achados)} achados", flush=True)
    with open("saida_teste/validacao.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(linhas[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(linhas)
    docs = defaultdict(set)
    for l in linhas:
        docs[l["regra"]].add(l["arquivo"])
    with open("saida_teste/validacao_resumo.txt", "w", encoding="utf-8") as fh:
        fh.write(f"Lote {args.lote} — raio {args.raio_mm} mm — {len(linhas)} achados\n")
        fh.write(f"{'regra':8} {'achados':>8} {'docs':>5} {'c/marca':>8}\n")
        for r in sorted(por_regra):
            c = por_regra[r]
            fh.write(f"{r:8} {c['achados']:8d} {len(docs[r]):5d} {c['com_marca_vermelha_ate_%dmm' % args.raio_mm]:8d}\n")
    print(open("saida_teste/validacao_resumo.txt", encoding="utf-8").read())


if __name__ == "__main__":
    main()
