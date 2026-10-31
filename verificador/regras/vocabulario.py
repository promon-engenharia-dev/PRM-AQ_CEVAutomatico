"""Família G — consistência de vocabulário (VOC)."""
from __future__ import annotations

import re
from collections import defaultdict

from ..config import normalizar, sem_acentos
from ..extracao import dentro


def _linhas_desenho(ctx):
    """Linhas fora do carimbo, das tabelas e dos blocos de texto corrido."""
    for pag in ctx.doc.paginas:
        areas = [t.area for t in pag.tabelas] + [b.area for b in ctx.blocos[pag.indice]]
        if pag.carimbo:
            areas.append(pag.carimbo.area)
        for l in pag.linhas:
            if not any(dentro(l, a) for a in areas):
                yield pag.indice, l


def verificar(ctx):
    if ctx.ativa("VOC-01"):
        p = ctx.p("VOC-01")
        curtas = [(pg, l) for pg, l in _linhas_desenho(ctx) if len(l.texto.split()) <= p["max_palavras_linha"]]
        for grupo in p["grupos_sinonimos"]:
            if not grupo.get("ativo", True):
                continue
            ocorr = defaultdict(list)
            for pg, l in curtas:
                t = normalizar(l.texto)
                for termo in grupo["termos"]:
                    if re.search(r"(?<![A-Z])" + re.escape(normalizar(termo)) + r"(?![A-Z])", t):
                        ocorr[termo].append((pg, l))
            if len(ocorr) > 1:
                minoria = min(ocorr, key=lambda k: len(ocorr[k]))
                termos = " × ".join(f'"{k}" ({len(v)}×)' for k, v in ocorr.items())
                por_pag = defaultdict(list)
                for pg, l in ocorr[minoria]:
                    por_pag[pg].append(l)
                for pg, ls in por_pag.items():
                    ctx.add("VOC-01", pg, ls[0].bbox, extras=[l.bbox for l in ls[1:]], termos=termos)

    if ctx.ativa("VOC-02"):
        p = ctx.p("VOC-02")["acentuacao"]
        exc = set(p["excecoes"])
        formas = defaultdict(lambda: defaultdict(list))
        for pag in ctx.doc.paginas:
            for l in pag.linhas:
                for w in re.findall(r"[A-ZÀ-Ý]{%d,}" % p["palavras_minimas_len"], l.texto.upper()):
                    formas[sem_acentos(w)][w].append((pag.indice, l))
        for base, var in formas.items():
            if len(var) < 2 or base in exc:
                continue
            com = [w for w in var if w != base]
            if base in var and com:
                correta = max(com, key=lambda w: len(var[w]))
                pg, l = var[base][0]
                ctx.add("VOC-02", pg, l.bbox, forma_errada=base, forma_correta=correta)
