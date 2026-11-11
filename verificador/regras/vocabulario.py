"""Família G — consistência de vocabulário (VOC)."""
from __future__ import annotations

import os
import re
import sys
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

    if ctx.ativa("VOC-04"):
        _ortografia(ctx)


# VOC-04 -------------------------------------------------------------------

_DICIONARIOS: dict = {}


def _arquivo(relativo: str, base: str) -> str:
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, relativo)
    return os.path.join(base, relativo)


def _palavras(caminho: str) -> set[str]:
    if not os.path.isfile(caminho):
        return set()
    with open(caminho, encoding="utf-8") as f:
        return {s.strip().lower() for s in f if s.strip() and not s.startswith("#")}


def _corretor(ctx):
    from spellchecker import SpellChecker     # dicionário local, embutido no pacote (sem rede)
    p = ctx.p("VOC-04")
    chave = (p["dicionario"], p["distancia_max"])
    if chave not in _DICIONARIOS:
        _DICIONARIOS[chave] = SpellChecker(language=p["dicionario"], distance=p["distancia_max"])
    raiz = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    conhecidas = _palavras(_arquivo(p["glossario"], raiz))
    conhecidas |= _palavras(os.path.join(os.path.dirname(ctx.cfg.caminho), p["glossario_local"]))
    if p["usar_titulos_da_ld"] and getattr(ctx, "ld", None) is not None:
        rx = re.compile(p["regex_palavra"])
        conhecidas |= {w.lower() for d in ctx.ld.docs for w in rx.findall(d.titulo or "")}
    return _DICIONARIOS[chave], conhecidas


def _distancia(a: str, b: str) -> int:
    """Damerau-Levenshtein (troca de letras vizinhas conta 1)."""
    d = [[i + j if i * j == 0 else 0 for j in range(len(b) + 1)] for i in range(len(a) + 1)]
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (a[i - 1] != b[j - 1]))
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)
    return d[-1][-1]


def _sugerir(lw: str, sp, conhecidas: set, p) -> str | None:
    """Até duas correções. Prefere o glossário e a LD (forma brasileira e termo técnico) ao dicionário."""
    do_dic = [w for w in sorted(sp.candidates(lw) or [], key=lambda w: -sp.word_usage_frequency(w)) if w != lw]
    if p["ignorar_so_acento"] and any(sem_acentos(w.upper()) == sem_acentos(lw.upper()) for w in do_dic):
        return None                                  # só falta acento (NIVEL × NÍVEL): não aponta
    d = p["distancia_glossario"]
    do_glos = sorted(w for w in conhecidas if abs(len(w) - len(lw)) <= d and _distancia(lw, w) <= d)
    cands = do_glos or do_dic
    return " ou ".join(cands[:p["max_sugestoes"]]) if cands else None


def _ortografia(ctx):
    p = ctx.p("VOC-04")
    sp, conhecidas = _corretor(ctx)
    rx = re.compile(p["regex_palavra"])
    sugestoes: dict = {}
    por_pag = defaultdict(list)
    for pag in ctx.doc.paginas:
        car = pag.carimbo.area if pag.carimbo else None
        for l in pag.linhas:
            if dentro(l, car):
                continue
            for w in rx.findall(l.texto):
                lw = w.lower()
                if lw in conhecidas or lw in sp:
                    continue
                if lw not in sugestoes:
                    sugestoes[lw] = _sugerir(lw, sp, conhecidas, p)
                if sugestoes[lw]:
                    por_pag[pag.indice].append((w, sugestoes[lw], l.bbox))
    for pg, ocorr in por_pag.items():
        (w, s, alvo), resto = ocorr[0], ocorr[1:]
        pares = list(dict.fromkeys((a.upper(), b.upper()) for a, b, _ in ocorr))
        if len(pares) == 1:
            ctx.add("VOC-04", pg, alvo, extras=[r for *_, r in resto], palavra=w.upper(), sugestao=s.upper())
            continue
        lista = "; ".join(f"{a} → {b}" for a, b in pares[:p["max_palavras_listadas"]])
        if len(pares) > p["max_palavras_listadas"]:
            lista += f" e mais {len(pares) - p['max_palavras_listadas']}"
        ctx.add("VOC-04", pg, alvo, chave="comentario_agrupado", extras=[r for *_, r in resto], palavras=lista)
