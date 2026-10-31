"""Prepara a revisão assistida (versão Claude) de um PDF.

Roda a versão offline (mesmo regras.json) e grava, numa pasta de trabalho, o que o Claude
precisa para revisar: imagens das folhas (inteira + recortes ampliados), texto com posição
em mm, campos do carimbo, achados offline e o texto do critério de projeto.

Uso:  python -X utf8 ferramentas/preparar_revisao.py arquivo.pdf [--criterio arquivo.pdf|.docx]
                                                     [--ld LD.xlsx] [--sem-ld] [--pasta trabalho]
Saída: <pasta do PDF>/<nome>_revisao/  (fora do Git: contém imagens do documento)
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import sys
import zipfile

import fitz

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from verificador import nucleo  # noqa: E402
from verificador.config import Config  # noqa: E402
from verificador.regras import executar  # noqa: E402


def _mm(cfg, v: float) -> float:
    return round(v * cfg["unidades"]["pt_para_mm"], 1)


def _rect_mm(cfg, r) -> list[float]:
    return [_mm(cfg, r.x0), _mm(cfg, r.y0), _mm(cfg, r.x1), _mm(cfg, r.y1)]


def renderizar(pdf: str, pasta: str, cfg: Config) -> list[dict]:
    """Folha inteira em baixa resolução e recortes sobrepostos em alta, todos na orientação de exibição."""
    r = cfg["revisao_assistida"]["renderizacao"]
    colunas, linhas = r["recortes"]
    indice = []
    with fitz.open(pdf) as doc:
        for page in doc:
            n = page.number + 1
            visao = page.get_pixmap(dpi=r["dpi_folha"])
            visao.save(os.path.join(pasta, f"folha_{n:02d}.png"))
            cheia = page.get_pixmap(dpi=r["dpi_recorte"])
            px_mm = r["dpi_recorte"] / 25.4
            w, h = cheia.width / colunas, cheia.height / linhas
            folga_x, folga_y = w * r["sobreposicao_rel"], h * r["sobreposicao_rel"]
            recortes = []
            for li in range(linhas):
                for co in range(colunas):
                    area = fitz.IRect(int(max(0, co * w - folga_x)), int(max(0, li * h - folga_y)),
                                      int(min(cheia.width, (co + 1) * w + folga_x)),
                                      int(min(cheia.height, (li + 1) * h + folga_y)))
                    rec = fitz.Pixmap(cheia.colorspace, area, cheia.alpha)
                    rec.copy(cheia, area)
                    rec.set_origin(0, 0)
                    nome = f"folha_{n:02d}_L{li + 1}C{co + 1}.png"
                    rec.save(os.path.join(pasta, nome))
                    recortes.append({"arquivo": nome, "retangulo_mm": [round(v / px_mm, 1) for v in
                                                                      (area.x0, area.y0, area.x1, area.y1)]})
            indice.append({"folha": n, "imagem": f"folha_{n:02d}.png",
                           "tamanho_mm": [_mm(cfg, page.rect.width), _mm(cfg, page.rect.height)],
                           "recortes": recortes})
    return indice


def texto_criterio(caminho: str) -> str:
    if caminho.lower().endswith(".docx"):
        with zipfile.ZipFile(caminho) as z:
            xml = z.read("word/document.xml").decode("utf-8")
        xml = re.sub(r"</w:p>", "\n", xml)
        return re.sub(r"<[^>]+>", "", xml)
    with fitz.open(caminho) as doc:
        return "\n".join(f"--- página {p.number + 1} ---\n{p.get_text()}" for p in doc)


def procurar_criterios(pdf: str, cfg: Config, niveis: int = 4) -> list[str]:
    cp = cfg["revisao_assistida"]["criterio_projeto"]
    achados, pasta = [], os.path.dirname(os.path.abspath(pdf))
    for _ in range(niveis + 1):
        try:
            nomes = os.listdir(pasta)
        except OSError:
            break
        for n in nomes:
            if os.path.splitext(n)[1].lower() in cp["extensoes"] and any(
                    fnmatch.fnmatch(n.upper(), p.upper()) for p in cp["padroes_nome"]):
                achados.append(os.path.join(pasta, n))
        pasta = os.path.dirname(pasta)
    return achados


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--criterio", help="critério de projeto da operação (.pdf ou .docx)")
    ap.add_argument("--ld")
    ap.add_argument("--sem-ld", action="store_true")
    ap.add_argument("--pasta", help="pasta de trabalho (padrão: <nome>_revisao ao lado do PDF)")
    args = ap.parse_args()

    cfg = Config()
    base = os.path.splitext(os.path.basename(args.pdf))[0]
    pasta = args.pasta or os.path.join(os.path.dirname(os.path.abspath(args.pdf)), base + "_revisao")
    os.makedirs(pasta, exist_ok=True)

    op = nucleo.Opcoes(ld=args.ld, sem_ld=args.sem_ld)
    pre = nucleo.preparar(args.pdf, cfg, op)
    ficha = nucleo.ficha_inicial(pre, cfg)
    achados = executar(pre.doc, cfg, ficha, pre.ld)

    with open(os.path.join(pasta, "offline.json"), "w", encoding="utf-8") as f:
        json.dump([{"regra": a.regra, "severidade": a.severidade, "folha": a.pagina + 1, "comentario": a.texto,
                    "retangulo_mm": _rect_mm(cfg, a.alvo), "ocorrencias": 1 + len(a.extras)} for a in achados],
                  f, ensure_ascii=False, indent=1)

    for p in pre.doc.paginas:
        with open(os.path.join(pasta, f"folha_{p.indice + 1:02d}_texto.tsv"), "w", encoding="utf-8") as f:
            f.write("x0_mm\ty0_mm\tx1_mm\ty1_mm\tcorpo_pt\ttexto\n")
            for l in sorted(p.linhas, key=lambda l: (round(l.bbox.y0 / 10), l.bbox.x0)):
                f.write("\t".join(str(v) for v in _rect_mm(cfg, l.bbox)) + f"\t{l.tamanho:.1f}\t{l.texto}\n")

    car = pre.doc.paginas[0].carimbo if pre.doc.paginas else None
    contexto = {
        "pdf": os.path.abspath(args.pdf),
        "operacao": pre.operacao,
        "ld": pre.caminho_ld,
        "ficha_deduzida": ficha,
        "carimbo": {"modelo": car.modelo, "campos": {k: c.valor for k, c in car.campos.items()}} if car else None,
        "folhas": renderizar(args.pdf, pasta, cfg),
        "criterios_revisao": {k: v["nome"] for k, v in cfg["revisao_assistida"]["criterios"].items()},
        "avisos": pre.avisos,
    }
    criterio = args.criterio
    candidatos = [] if criterio else procurar_criterios(args.pdf, cfg)
    if not criterio and len(candidatos) == 1:
        criterio = candidatos[0]
    contexto["criterio_projeto"] = criterio
    contexto["criterio_candidatos"] = candidatos
    if criterio:
        with open(os.path.join(pasta, "criterio_projeto.txt"), "w", encoding="utf-8") as f:
            f.write(texto_criterio(criterio))
    with open(os.path.join(pasta, "contexto.json"), "w", encoding="utf-8") as f:
        json.dump(contexto, f, ensure_ascii=False, indent=1)

    print(f"Pasta de trabalho: {pasta}")
    print(f"{len(achados)} achado(s) offline · {len(contexto['folhas'])} folha(s) · "
          f"critério de projeto: {os.path.basename(criterio) if criterio else 'não encontrado'}"
          + (f" ({len(candidatos)} candidatos)" if len(candidatos) > 1 else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
