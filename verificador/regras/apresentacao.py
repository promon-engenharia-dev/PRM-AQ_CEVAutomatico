"""Família F — apresentação (APR) e cotas de nível (TAG-05)."""
from __future__ import annotations

import re
from collections import Counter, defaultdict

import fitz

from ..config import normalizar
from ..extracao import dentro


def _escala(texto: str) -> int | None:
    m = re.search(r"1\s*[:/]\s*(\d+)", texto)
    return int(m.group(1)) if m else None


def verificar(ctx):
    cfg = ctx.cfg
    eh_prancha = ctx.classe in cfg["ficha"]["deducao_automatica"]["classes_prancha"]
    for pag in ctx.doc.paginas:
        area_car = pag.carimbo.area if pag.carimbo else None

        if ctx.ativa("APR-04"):
            p = ctx.p("APR-04")
            tol = cfg.mm_para_pt(p["duplicado"]["distancia_max_mm"])
            vistos, n = set(), 0
            ordenadas = sorted(pag.linhas, key=lambda l: (l.texto, l.bbox.x0, l.bbox.y0))
            for a, b in zip(ordenadas, ordenadas[1:]):
                if a.texto == b.texto and abs(a.bbox.x0 - b.bbox.x0) <= tol and abs(a.bbox.y0 - b.bbox.y0) <= tol:
                    chave = (a.texto, round(a.bbox.x0), round(a.bbox.y0))
                    if chave in vistos:
                        continue
                    vistos.add(chave)
                    n += 1
                    if n <= p["max_por_pagina"]:
                        ctx.add("APR-04", pag.indice, a.bbox, texto=a.texto[:40])

        if ctx.ativa("APR-05"):
            margem = cfg.mm_para_pt(ctx.p("APR-05")["borda"]["margem_mm"])
            util = fitz.Rect(pag.rect.x0 + margem, pag.rect.y0 + margem, pag.rect.x1 - margem, pag.rect.y1 - margem)
            cortadas = [l for l in pag.linhas if not util.contains(l.bbox)]
            if cortadas:
                ctx.add("APR-05", pag.indice, cortadas[0].bbox & pag.rect,
                        extras=[l.bbox & pag.rect for l in cortadas[1:]], texto=cortadas[0].texto[:40])

        if ctx.ativa("APR-06"):
            v = ctx.p("APR-06")["vistas"]
            rx_persp = re.compile(v["regex_perspectiva"])
            rx_exc = re.compile(v["regex_excluir"])
            convencao = any(vi.escala is not None for vi in pag.vistas)
            for vista in (pag.vistas if convencao else []):
                tit = normalizar(vista.titulo.texto, acentos=True)
                if vista.escala is not None or rx_exc.match(tit):
                    continue
                if rx_persp.match(tit):
                    ctx.add("APR-06", pag.indice, vista.titulo.bbox, chave="comentario_perspectiva",
                            severidade=ctx.p("APR-06")["severidade_perspectiva"])
                else:
                    ctx.add("APR-06", pag.indice, vista.titulo.bbox, vista=vista.titulo.texto)

        escalas_vistas = sorted({e for vi in pag.vistas if vi.escala and (e := _escala(vi.escala.texto))})
        if ctx.ativa("APR-07") and pag.carimbo and "escala" in pag.carimbo.campos and escalas_vistas:
            campo = pag.carimbo.campos["escala"]
            val = normalizar(campo.valor, acentos=True)
            multiplas = {normalizar(x, acentos=True) for x in ctx.p("APR-07")["escala"]["valor_multiplas"]}
            n_car = _escala(val)
            alvo = campo.bbox if campo.linhas else pag.carimbo.rotulos["escala"].bbox
            texto_vistas = ", ".join(f"1 : {e}" for e in escalas_vistas)
            if val in multiplas:
                if len(escalas_vistas) == 1:
                    pass        # “INDICADA” com escala única é aceitável
            elif n_car is not None and set(escalas_vistas) != {n_car}:
                ctx.add("APR-07", pag.indice, alvo, escala_carimbo=campo.valor, escalas_vistas=texto_vistas)

        if ctx.ativa("APR-08"):
            p = ctx.p("APR-08")["escala"]
            rx_ok = re.compile(p["regex_formato_ok"])
            for vi in pag.vistas:
                if vi.escala and normalizar(vi.escala.texto) != "SEM ESCALA" and not rx_ok.search(vi.escala.texto):
                    n = _escala(vi.escala.texto)
                    if n:
                        ctx.add("APR-08", pag.indice, vi.escala.bbox, n=n)

        if ctx.ativa("APR-10") and eh_prancha:
            rx_ok = [re.compile(r) for r in ctx.p("APR-10")["fonte"]["italico_permitido_regex"]]
            ital = sorted([l for l in pag.linhas if l.italico and not dentro(l, area_car)
                           and not any(r.search(l.texto) for r in rx_ok)], key=lambda l: -l.tamanho)
            if ital:
                ctx.add("APR-10", pag.indice, ital[0].bbox, extras=[l.bbox for l in ital[1:]])

    if ctx.ativa("TAG-05"):
        _cotas_nivel(ctx)


def _assinatura(texto: str):
    m = re.match(r"^EL(\.?)(\s*)(-?\d+)(?:,(\d+))?(.*)$", texto.strip())
    if not m:
        return None
    return (m.group(1) == ".", len(m.group(2)) > 0, len(m.group(4) or ""), m.group(5).strip() != "")


def _cotas_nivel(ctx):
    p = ctx.p("TAG-05")["cota_nivel"]
    rx = re.compile(p["regex_candidato"])
    ocorr = []
    for pag in ctx.doc.paginas:
        area_car = pag.carimbo.area if pag.carimbo else None
        areas_txt = [b.area for b in ctx.blocos[pag.indice]]
        for l in pag.linhas:
            if dentro(l, area_car) or any(dentro(l, a) for a in areas_txt) or not rx.match(l.texto):
                continue
            s = _assinatura(l.texto)
            if s:
                ocorr.append((s, pag.indice, l))
    if len(ocorr) < p["minimo_ocorrencias"]:
        return
    cont = Counter(s for s, _, _ in ocorr)
    dominante, _ = cont.most_common(1)[0]
    exemplo = next(l.texto for s, _, l in ocorr if s == dominante)
    grupos = defaultdict(list)
    for s, pag, l in ocorr:
        if s != dominante and cont[s] / len(ocorr) <= p["fracao_minoritaria"]:
            grupos[(pag, s)].append(l)
    for (pag, _), ls in grupos.items():
        ctx.add("TAG-05", pag, ls[0].bbox, extras=[l.bbox for l in ls[1:]], texto=ls[0].texto, exemplo=exemplo)
