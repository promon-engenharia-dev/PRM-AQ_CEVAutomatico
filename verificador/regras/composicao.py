"""Composição da folha: títulos de vista (APR-12), alinhamento de vistas (APR-13),
tabelas sobrepostas (TAB-07) e código de emissão do histórico (CAR-14)."""
from __future__ import annotations

import itertools

import fitz

from ..config import normalizar


def verificar(ctx):
    cfg = ctx.cfg
    eh_prancha = ctx.classe in cfg["ficha"]["deducao_automatica"]["classes_prancha"]
    mm = cfg.mm_para_pt
    pt_mm = cfg["unidades"]["pt_para_mm"]
    for pag in ctx.doc.paginas:
        if eh_prancha and ctx.ativa("APR-12"):
            sug = ctx.p("APR-12")["sugestoes"]
            for v in pag.vistas:
                if v.so_nivel:
                    t = v.titulo.texto.strip()
                    modelo = sug.get(normalizar(t, acentos=True), sug["*"])
                    ctx.add("APR-12", pag.indice, v.titulo.bbox, titulo=t, sugestao=modelo.format(titulo=t))

        if eh_prancha and ctx.ativa("APR-13"):
            lo, hi = (mm(x) for x in ctx.p("APR-13")["desalinhamento_mm"])
            tipos = set(ctx.p("APR-13")["tipos_vista"])
            com_escala = [v for v in pag.vistas if v.escala is not None and v.tipo in tipos]
            for a, b in itertools.combinations(sorted(com_escala, key=lambda v: v.titulo.bbox.x0), 2):
                ta, tb = a.titulo.bbox, b.titulo.bbox
                dy = tb.y1 - ta.y1                     # pela linha de base do título
                if ta.x1 < tb.x0 and lo <= abs(dy) <= hi:
                    ctx.add("APR-13", pag.indice, tb, a=b.titulo.texto, b=a.titulo.texto,
                            dy=f"{abs(dy) * pt_mm:.1f}".replace(".", ","), lado="abaixo" if dy > 0 else "acima")

        if ctx.ativa("TAB-07") and pag.tabelas:
            _tabelas_encobertas(ctx, pag)

        if ctx.ativa("CAR-14") and pag.carimbo and pag.indice == 0:
            validos = ctx.p("CAR-14")["codigos_emissao"]
            for h in pag.carimbo.historico:
                cod = h.valor("finalidade").strip().upper()
                if cod and cod not in validos:
                    ctx.add("CAR-14", pag.indice, h.celulas["finalidade"].bbox, codigo=cod,
                            rev=h.valor("revisao") or "?", validos=", ".join(validos))


def _preenchimentos(ctx, pag) -> list[fitz.Rect]:
    desenhos, m = ctx.desenhos(pag.indice)
    return [d["rect"] * m for d in desenhos
            if d.get("fill") and d.get("type") in ("f", "fs") and (d.get("fill_opacity") or 1) > 0.5]


def _cortada(l, fills, lo, hi) -> bool:
    """Um preenchimento começa (ou termina) dentro da linha e cobre parte da altura dela."""
    b = l.bbox
    for r in fills:
        if r.x1 <= b.x0 or r.x0 >= b.x1:
            continue
        if b.y0 < r.y0 < b.y1 and r.y1 >= b.y1:
            frac = (b.y1 - r.y0) / b.height
        elif b.y0 < r.y1 < b.y1 and r.y0 <= b.y0:
            frac = (r.y1 - b.y0) / b.height
        else:
            continue
        if lo <= frac <= hi and min(r.x1, b.x1) - max(r.x0, b.x0) >= 0.3 * b.width:
            return True
    return False


def _tabelas_encobertas(ctx, pag):
    lo, hi = ctx.p("TAB-07")["fracao_coberta"]
    fills = _preenchimentos(ctx, pag)
    for t in pag.tabelas:
        # largura real da tabela (título + cabeçalho): a área estimada pode avançar sobre o desenho
        tb = t.titulo.bbox
        alcance = 1.5 * tb.width          # o cabeçalho pode pegar TAGs do desenho ao lado
        cab = [c.bbox for c in t.cabecalho if tb.x0 - alcance <= c.bbox.x0 and c.bbox.x1 <= tb.x1 + alcance]
        x0 = min([tb.x0] + [c.x0 for c in cab]) - 3
        x1 = max([tb.x1] + [c.x1 for c in cab]) + 3
        afetadas = [l for reg in t.linhas for ls in reg.celulas.values() for l in ls
                    if x0 <= l.cx <= x1 and _cortada(l, fills, lo, hi)]
        if afetadas:
            maior = max(afetadas, key=lambda l: len(l.texto))
            ctx.add("TAB-07", pag.indice, maior.bbox, extras=[l.bbox for l in afetadas if l is not maior],
                    tabela=t.nome.title(), trecho=maior.texto[:40])
