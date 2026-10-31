"""Grava os achados como anotações vermelhas, em salvamento INCREMENTAL.

O arquivo de saída começa como cópia byte a byte do original; as anotações
são acrescentadas no fim (saveIncr). Assim o conteúdo original, as anotações
preexistentes e eventuais assinaturas digitais ficam intactos.
"""
from __future__ import annotations

import html
import shutil

import fitz

from .config import Config
from .modelo import Achado


def _pdf_str(s: str) -> str:
    return "(" + s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") + ")"


def numerar(achados: list[Achado]) -> list[Achado]:
    """CV-AQ-nnn só para o que vai ao PDF; os CORRETO da revisão assistida ficam no fim, sem índice."""
    ordem = sorted(achados, key=lambda a: (a.severidade == "CORRETO", a.pagina, round(a.alvo.y0 / 20), a.alvo.x0))
    i = 0
    for a in ordem:
        if a.severidade != "CORRETO":
            i += 1
        a.indice = i if a.severidade != "CORRETO" else 0
    return ordem


def tag(cfg: Config, a: Achado) -> str:
    if not a.indice:
        return "—"
    t = cfg["anotacao"]["tag_comentario"]
    return t["formato"].format(especialidade=t["especialidade"], indice=a.indice).rstrip(" —-")


def _tamanho_caixa(texto: str, cfg: Config) -> tuple[float, float]:
    te = cfg["anotacao"]["texto_explicativo"]
    largura = cfg.mm_para_pt(te["largura_max_mm"])
    fs = 10
    por_linha = max(10, int(largura / (fs * 0.52)))
    linhas = 0
    for par in texto.split("\n"):
        linhas += max(1, -(-len(par) // por_linha))
    return largura, linhas * fs * 1.4 + 12


def _posicionar(alvo: fitz.Rect, w: float, h: float, pagina: fitz.Rect, ocupados: list[fitz.Rect],
                obstaculos: list[fitz.Rect] = ()) -> fitz.Rect:
    """Primeiro tenta um lugar sem outras caixas nem textos da folha; depois, só sem outras caixas."""
    for evitar in (list(ocupados) + list(obstaculos), ocupados):
        r = _tentar(alvo, w, h, pagina, evitar)
        if r is not None:
            return r
    return _encostar(alvo, w, h, pagina)


def _tentar(alvo, w, h, pagina, evitar):
    for d in (40, 100, 180):
        r = _tentar_distancia(alvo, w, h, pagina, evitar, d)
        if r is not None:
            return r
    return None


def _tentar_distancia(alvo, w, h, pagina, evitar, d):
    cands = [
        fitz.Rect(alvo.x1 + d, alvo.y0 - h - d / 2, alvo.x1 + d + w, alvo.y0 - d / 2),   # acima à direita
        fitz.Rect(alvo.x0 - d - w, alvo.y0 - h - d / 2, alvo.x0 - d, alvo.y0 - d / 2),   # acima à esquerda
        fitz.Rect(alvo.x1 + d, alvo.y1 + d / 2, alvo.x1 + d + w, alvo.y1 + d / 2 + h),   # abaixo à direita
        fitz.Rect(alvo.x0 - d - w, alvo.y1 + d / 2, alvo.x0 - d, alvo.y1 + d / 2 + h),   # abaixo à esquerda
    ]
    for desloc in range(0, 12):
        for c in cands:
            r = fitz.Rect(c.x0, c.y0 + desloc * (h + 6) * (1 if c.y0 > alvo.y0 else -1), c.x1, 0)
            r.y1 = r.y0 + h
            if pagina.contains(r) and not r.intersects(alvo) and not any(r.intersects(o) for o in evitar):
                return r
    return None


def _encostar(alvo, w, h, pagina):
    """Sem espaço livre: encosta na página, ainda sem cobrir o alvo se possível."""
    d = 40
    r = fitz.Rect(alvo.x1 + d, alvo.y0 - h - d / 2, alvo.x1 + d + w, alvo.y0 - d / 2)
    r.x0, r.x1 = min(max(r.x0, pagina.x0 + 5), pagina.x1 - w - 5), 0
    r.x1 = r.x0 + w
    r.y0 = min(max(r.y0, pagina.y0 + 5), pagina.y1 - h - 5)
    r.y1 = r.y0 + h
    return r


def _marcar(doc, page, alvo: fitz.Rect, marca: fitz.Rect, modo: str, mt: dict, autor: str, cor, nm: str):
    """Marca uma ocorrência: faixa translúcida sobre o texto, retângulo translúcido ou nuvem em volta."""
    derot = page.derotation_matrix
    if modo == "nuvem":
        nuv = mt["nuvem"]
        pts = [fitz.Point(marca.x0, marca.y0), fitz.Point(marca.x1, marca.y0),
               fitz.Point(marca.x1, marca.y1), fitz.Point(marca.x0, marca.y1), fitz.Point(marca.x0, marca.y0)]
        an = page.add_polygon_annot([p * derot for p in pts])
        an.set_colors(stroke=cor)
        an.set_border(width=nuv["bs_largura"], clouds=nuv["be"]["I"])
        an.set_info(title=autor, subject=nuv["subj"], content="")
        an.update()
        doc.xref_set_key(an.xref, "IT", "/" + nuv["it"])
    elif modo == "retangulo_translucido":
        ret = mt["retangulo"]
        an = page.add_rect_annot(fitz.Rect(marca * derot).normalize())
        an.set_colors(stroke=cor, fill=cor)
        an.set_border(width=ret["bs_largura"])
        an.set_opacity(ret["opacidade"])
        an.set_info(title=autor, subject=ret["subj"], content="")
        an.update()
    elif modo == "faixa_translucida":
        fx = mt["faixa"]
        if alvo.width >= alvo.height:      # texto horizontal: faixa no eixo da linha
            p1, p2 = fitz.Point(alvo.x0, (alvo.y0 + alvo.y1) / 2), fitz.Point(alvo.x1, (alvo.y0 + alvo.y1) / 2)
            esp = alvo.height
        else:                              # texto vertical
            p1, p2 = fitz.Point((alvo.x0 + alvo.x1) / 2, alvo.y0), fitz.Point((alvo.x0 + alvo.x1) / 2, alvo.y1)
            esp = alvo.width
        an = page.add_line_annot(p1 * derot, p2 * derot)
        an.set_colors(stroke=cor)
        an.set_border(width=max(esp * fx["espessura_relativa"], fx["espessura_min_pt"]))
        an.set_opacity(fx["opacidade"])
        an.set_info(title=autor, subject=fx["subj"], content="")
        an.update()
    else:
        return
    doc.xref_set_key(an.xref, "NM", _pdf_str(nm))


def anotar(origem: str, destino: str, achados: list[Achado], cfg: Config,
           obstaculos: dict[int, list[fitz.Rect]] | None = None) -> None:
    acfg = cfg["anotacao"]
    te = acfg["texto_explicativo"]
    mt = acfg["marcacao_trecho"]
    nuv = mt["nuvem"]
    seta = acfg["seta"]
    autor = acfg["autor"]
    vermelho = tuple(acfg["cor_rgb"])
    if origem != destino:
        shutil.copyfile(origem, destino)
    doc = fitz.open(destino)
    ocupados: dict[int, list[fitz.Rect]] = {}
    for a in achados:
        page = doc[a.pagina]
        prect = fitz.Rect(page.rect)
        derot = page.derotation_matrix
        ocup = ocupados.setdefault(a.pagina, [])
        texto = f"{tag(cfg, a)} — {a.texto}"
        nm = f"{tag(cfg, a)}|{a.regra}|{a.severidade}"

        folga = cfg.mm_para_pt(nuv["folga_mm"])
        modo = mt["modo_achado_com_regiao"] if a.regiao else mt["modo_achado_pontual"]
        marcas = []
        for k, r in enumerate([a.alvo] + list(a.extras)):
            alvo = fitz.Rect(r) & prect
            if alvo.is_empty:
                alvo = fitz.Rect(r.x0, r.y0, r.x0 + 5, r.y0 + 5) & prect
            marca = fitz.Rect(alvo.x0 - folga, alvo.y0 - folga, alvo.x1 + folga, alvo.y1 + folga) & prect
            _marcar(doc, page, alvo, marca, modo, mt, autor, vermelho, f"{nm}|marca{k}")
            marcas.append(marca)

        w, h = _tamanho_caixa(texto, cfg)
        caixa = _posicionar(marcas[0], w, h, prect, ocup, (obstaculos or {}).get(a.pagina, ()))
        ocup.append(caixa)
        cx, cy = (caixa.x0 + caixa.x1) / 2, (caixa.y0 + caixa.y1) / 2

        def ligacao(m):
            ponta = fitz.Point(min(max(cx, m.x0), m.x1), min(max(cy, m.y0), m.y1))
            joelho = fitz.Point(min(max(ponta.x, caixa.x0), caixa.x1), min(max(ponta.y, caixa.y0), caixa.y1))
            return ponta, joelho

        ponta, joelho = ligacao(marcas[0])
        if seta.get("ativa"):
            # a 1ª ocorrência já recebe a seta da própria caixa (callout); as demais ganham seta separada,
            # as mais próximas primeiro, até o limite configurado
            ordem = sorted(marcas[1:], key=lambda m: abs(m.x0 - cx) + abs(m.y0 - cy))
            for k, m in enumerate(ordem[: acfg["max_setas_por_achado"] - 1], 1):
                pt, jo = ligacao(m)
                st = page.add_line_annot(jo * derot, pt * derot)
                st.set_colors(stroke=vermelho)
                st.set_border(width=seta["bs_largura"])
                st.set_line_ends(fitz.PDF_ANNOT_LE_NONE, fitz.PDF_ANNOT_LE_OPEN_ARROW)
                st.set_info(title=autor, subject=seta["subj"], content="")
                st.update()
                doc.xref_set_key(st.xref, "IT", "/" + seta["it"])
                doc.xref_set_key(st.xref, "NM", _pdf_str(f"{nm}|seta{k}"))
        caixa_u = fitz.Rect(caixa * derot)
        caixa_u.normalize()
        ft = page.add_freetext_annot(
            caixa_u, texto, fontsize=10, fontname="helv",
            text_color=vermelho, fill_color=tuple(te["fundo_rgb"]), border_width=1,
            callout=[ponta * derot, joelho * derot], line_end=fitz.PDF_ANNOT_LE_OPEN_ARROW,
            rotate=page.rotation,
        )
        ft.set_info(title=autor, subject=te["subj"], content=texto)
        ft.update()
        x = ft.xref
        doc.xref_set_key(x, "IT", "/" + te["it"])
        doc.xref_set_key(x, "DA", _pdf_str(te["da"]))
        doc.xref_set_key(x, "DS", _pdf_str(te["ds"]))
        doc.xref_set_key(x, "LE", "/" + te["le"])
        rc = ('<?xml version="1.0"?><body xmlns="http://www.w3.org/1999/xhtml" '
              'xmlns:xfa="http://www.xfa.org/schema/xfa-data/1.0/" xfa:APIVersion="Acrobat:11.0.0" '
              f'xfa:spec="2.0.2" style="{te["ds"]}"><p>{html.escape(texto)}</p></body>')
        doc.xref_set_key(x, "RC", _pdf_str(rc))
        doc.xref_set_key(x, "NM", _pdf_str(nm))
    doc.saveIncr()
    doc.close()
