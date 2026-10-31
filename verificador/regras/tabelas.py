"""Família C — tabelas (TAB)."""
from __future__ import annotations

import re

import fitz

from ..config import normalizar
from .keynotes import analisar


def verificar(ctx):
    cfg = ctx.cfg
    doc = ctx.doc
    eh_prancha = ctx.classe in cfg["ficha"]["deducao_automatica"]["classes_prancha"]
    tabelas = [t for p in doc.paginas for t in p.tabelas]

    if ctx.ativa("TAB-01") and eh_prancha and len(tabelas) >= ctx.p("TAB-01")["minimo_tabelas_no_documento"]:
        a = analisar(ctx)
        usados = {re.match(r"[A-Z]+", c).group(0) for c in a.usos}
        nomes = [normalizar(t.nome, acentos=True) for t in tabelas]
        p0 = doc.paginas[0]
        ref = tabelas[0].area
        tem_ambiente = {}
        tipos_vista = {v.tipo for p in doc.paginas for v in p.vistas}
        for req in ctx.p("TAB-01")["obrigatorias"]:
            cond = req.get("exigir_se", {})
            if "prefixos" in cond and not (usados & set(cond["prefixos"])):
                continue
            if "tipos_vista" in cond and not tipos_vista & set(cond["tipos_vista"]):
                continue                      # ex.: quadros só nas plantas gerais, não em ampliações
            if "regex_linha" in cond:
                rx = cond["regex_linha"]
                if rx not in tem_ambiente:
                    tem_ambiente[rx] = any(re.match(rx, l.texto) for l in doc.todas_linhas())
                if not tem_ambiente[rx]:
                    continue
            if not any(re.match(req["regex"], n) for n in nomes):
                ctx.add("TAB-01", tabelas[0].pagina, fitz.Rect(ref.x0, ref.y0 - 20, ref.x1, ref.y0), tabela=req["nome"])

    for t in tabelas:
        if ctx.ativa("TAB-02") and t.cabecalho and not t.linhas:
            ctx.add("TAB-02", t.pagina, t.area, regiao=True, tabela=t.nome)

        if ctx.ativa("TAB-03") and re.match(r"^QUADRO DE ÁREAS", normalizar(t.nome, acentos=True)):
            textos = {normalizar(l.texto) for reg in t.linhas for ls in reg.celulas.values() for l in ls}
            faltam = [x for x in ctx.p("TAB-03")["quadro_areas"]["termos_obrigatorios"]
                      if not any(normalizar(x) in tx for tx in textos)]
            if faltam and textos:
                ctx.add("TAB-03", t.pagina, t.area, regiao=True)

        if ctx.ativa("TAB-04"):
            for u in ctx.p("TAB-04")["unidades"]:
                cabs = [c for c in t.cabecalho if re.search(u["cabecalho_regex"], c.texto, re.I)]
                if not cabs:
                    continue
                rx = re.compile(u["celula_regex"], re.I)
                cel = [l for reg in t.linhas for ls in reg.celulas.values() for l in ls
                       if any(c.bbox.x0 - 25 <= l.cx <= c.bbox.x1 + 25 for c in cabs) and rx.search(l.texto)]
                if cel:
                    area = fitz.Rect(cel[0].bbox)
                    for l in cel[1:]:
                        area |= l.bbox
                    ctx.add("TAB-04", t.pagina, area, regiao=True, unidade=u["unidade"])
