"""Família CON — informação faltante por vista — e TAGs de ambiente (TAG-01/02)."""
from __future__ import annotations

import re

import fitz

from ..extracao import dentro, mesma_linha
from ..tabelas import linhas_da_vista


def _tabela_menciona(ctx, rx: str) -> bool:
    r = re.compile(rx)
    return any(r.search(l.texto) for p in ctx.doc.paginas for t in p.tabelas
               for reg in t.linhas for ls in reg.celulas.values() for l in ls)


def _edificacao(ctx) -> bool:
    rx = re.compile(ctx.p("PRA-01")["regex_edificacao"])
    return any(rx.match(l.texto) for l in ctx.doc.todas_linhas())


def verificar(ctx):
    if ctx.classe not in ctx.cfg["ficha"]["deducao_automatica"]["classes_prancha"] or not _edificacao(ctx):
        return
    minimo = ctx.cfg["vistas_recorte"]["min_linhas_para_julgar"]
    for pag in ctx.doc.paginas:
        excl = ctx.areas_texto(pag)
        for v in pag.vistas:
            ls = linhas_da_vista(pag, v, excl)
            if len(ls) < minimo:
                continue                      # vista sem texto suficiente para julgar (ex.: só desenho)
            for codigo in ("CON-01", "CON-02", "CON-03", "CON-05"):
                p = ctx.p(codigo)
                if not ctx.ativa(codigo) or v.tipo not in p["tipos_vista"]:
                    continue
                if "exigir_se_tabela_regex" in p and not _tabela_menciona(ctx, p["exigir_se_tabela_regex"]):
                    continue
                rxs = [re.compile(r, re.I) for r in p["regex_presenca"]]
                if not any(r.search(l.texto) for l in ls for r in rxs):
                    ctx.add(codigo, pag.indice, v.titulo.bbox, vista=v.titulo.texto)
            if ctx.ativa("CON-04") and v.tipo in ctx.p("CON-04")["tipos_vista"]:
                _cotas_eixos(ctx, pag, v, ls)
            if ctx.ativa("CON-08") and v.tipo in ctx.p("CON-08")["tipos_vista"]:
                _pe_direito_corte(ctx, pag, v, ls)
        if ctx.ativa("CON-06") or ctx.ativa("CON-07"):
            _cotas_ambientes(ctx, pag, excl)
        if ctx.ativa("TAG-01") or ctx.ativa("TAG-02"):
            _tags_ambiente(ctx, pag, excl)


# CON-04 -------------------------------------------------------------------

def _sequencia(rotulos: list[str]) -> bool:
    """Rótulos de malha em ordem: 1, 2, 3… ou A, B, C… (pode pular, mas não voltar)."""
    if all(r.isdigit() for r in rotulos):
        vals = [int(r) for r in rotulos]
    elif all(r.isalpha() for r in rotulos):
        vals = [sum((ord(c) - 64) * 26 ** i for i, c in enumerate(reversed(r))) for r in rotulos]
    else:
        return False
    return all(b > a for a, b in zip(vals, vals[1:])) or all(b < a for a, b in zip(vals, vals[1:]))


def _cotas_eixos(ctx, pag, v, ls):
    p = ctx.p("CON-04")
    rx_bolha = re.compile(p["regex_bolha"])
    rx_cota = re.compile(p["regex_cota"])
    dist = p["distancia_max_cota_pt"]
    bolhas = [l for l in ls if l.tamanho >= p["tamanho_min_bolha_pt"] and rx_bolha.match(l.texto)]
    cotas = [l for l in ls if rx_cota.match(l.texto)]
    # linhas de bolhas (eixos verticais, rótulos lado a lado) e colunas (eixos horizontais)
    for eixo_h in (True, False):
        grupos: list[list] = []
        for b in sorted(bolhas, key=lambda l: (l.cy if eixo_h else l.cx)):
            chave = b.cy if eixo_h else b.cx
            if grupos and abs((grupos[-1][0].cy if eixo_h else grupos[-1][0].cx) - chave) <= 4:
                grupos[-1].append(b)
            else:
                grupos.append([b])
        for g in grupos:
            g.sort(key=lambda l: l.cx if eixo_h else l.cy)
            if len(g) < p["min_eixos"] or not _sequencia([l.texto for l in g]):
                continue
            for a, b in zip(g, g[1:]):
                lo, hi = (a.cx, b.cx) if eixo_h else (a.cy, b.cy)
                achou = any(
                    lo + 2 < (c.cx if eixo_h else c.cy) < hi - 2
                    and 4 < abs((c.cy - a.cy) if eixo_h else (c.cx - a.cx)) <= dist
                    and (c.horizontal == eixo_h)
                    for c in cotas)
                if not achou:
                    alvo = fitz.Rect(a.bbox) | b.bbox
                    ctx.add("CON-04", pag.indice, alvo, regiao=True, e1=a.texto, e2=b.texto)


# CON-06 / CON-07 / CON-08 ----------------------------------------------------

def _nome_ambiente(a, linhas) -> str:
    """Nome escrito logo acima do 'A= … m²' (a linha em caixa alta mais próxima)."""
    acima = [l for l in linhas if l.bbox.y1 <= a.bbox.y0 + 1 and abs(l.cx - a.cx) < 60 and a.bbox.y0 - l.bbox.y1 < 60
             and re.search(r"[A-ZÁ-Ú]{3}", l.texto) and not l.texto.startswith(("EL", "("))
             and not re.fullmatch(r"[A-Z]{2,3}[\s\-]?\d{2,3}[A-Z]?", l.texto)]
    return max(acima, key=lambda l: (l.tamanho, l.bbox.y0)).texto if acima else "?"


def _cotas_ambientes(ctx, pag, excl):
    from .apresentacao import _escala
    rx_a = re.compile(ctx.p("TAG-comum")["tag_ambiente"]["regex_area"])
    p6, p7 = ctx.p("CON-06"), ctx.p("CON-07")
    rx_cota = re.compile(p6["regex_cota"])
    rx_el = re.compile(p7["regex_nivel"])
    sem_dim, sem_el = [], []
    for v in pag.vistas:
        if v.tipo not in p6["tipos_vista"] or v.area is None:
            continue
        escala = (_escala(v.escala.texto) if v.escala else None) or p6["escala_padrao"]
        ls = linhas_da_vista(pag, v, excl)
        for a in ls:
            m = rx_a.match(a.texto)
            if not m:
                continue
            lado_m = float(m.group("valor").replace(",", ".")) ** 0.5
            raio = max(p6["raio_min_pt"], ctx.cfg.mm_para_pt(p6["fator_raio"] * lado_m * 1000 / escala))
            r = fitz.Rect(a.cx - raio, a.cy - raio, a.cx + raio, a.cy + raio)
            perto = [l for l in ls if l is not a and dentro(l, r)]
            nome = _nome_ambiente(a, perto)
            if ctx.ativa("CON-06"):
                # corrente de cotas: a largura pode estar em qualquer altura da vista, desde que na
                # faixa de colunas do ambiente; o comprimento, na faixa de linhas
                meio = raio * p6["fator_faixa"]
                cotas = [l for l in ls if rx_cota.match(l.texto)]
                largura = any(l.horizontal and abs(l.cx - a.cx) <= meio for l in cotas)
                comprimento = any(not l.horizontal and abs(l.cy - a.cy) <= meio for l in cotas)
                if not (largura and comprimento):
                    sem_dim.append((nome, a.bbox))
            if ctx.ativa("CON-07") and not any(rx_el.match(l.texto) for l in perto):
                sem_el.append((nome, a.bbox))
    _agrupado(ctx, "CON-06", pag, sem_dim)
    _agrupado(ctx, "CON-07", pag, sem_el)


def _pe_direito_corte(ctx, pag, v, ls):
    p = ctx.p("CON-08")
    rx_cota, rx_pd = re.compile(p["regex_cota"]), re.compile(p["regex_pd"])
    vertical = any(not l.horizontal and rx_cota.match(l.texto) for l in ls)
    if not vertical and not any(rx_pd.match(l.texto) for l in ls):
        ctx.add("CON-08", pag.indice, v.titulo.bbox, vista=v.titulo.texto)


# TAG-01 / TAG-02 -----------------------------------------------------------

def _tags_ambiente(ctx, pag, excl):
    t = ctx.p("TAG-comum")["tag_ambiente"]
    rx_a = re.compile(t["regex_area"])
    rx_pd = re.compile(t["regex_pd"])
    rx_cod = re.compile(t["regex_acabamento"])
    jan = t["janela_pt"]
    sem_pd, sem_acab = [], []
    for a in pag.linhas:
        if not rx_a.match(a.texto) or any(dentro(a, x) for x in excl):
            continue
        k = max(1.0, a.tamanho / t["janela_tamanho_ref_pt"])      # TAG em escala maior: janela maior
        lat, aci, aba = jan["lateral"] * k, jan["acima"] * k, jan["abaixo"] * k
        if not a.horizontal:                                       # TAG girada: o "acima" vira lateral
            lat, aci, aba = max(aci, aba), lat, lat
        r = fitz.Rect(a.bbox.x0 - lat, a.bbox.y0 - aci, a.bbox.x1 + lat, a.bbox.y1 + aba)
        viz = [l for l in pag.linhas if l is not a and dentro(l, r)]
        nome = next((l.texto for l in sorted(viz, key=lambda l: l.bbox.y0)
                     if l.bbox.y1 <= a.bbox.y0 + 1 and re.search(r"[A-ZÁ-Ú]{3}", l.texto)
                     and not rx_cod.fullmatch(l.texto) and not l.texto.startswith(("EL", "("))), "?")
        if ctx.ativa("TAG-01") and not any(rx_pd.match(l.texto) for l in viz):
            sem_pd.append((nome, a.bbox))
        n_acab = sum(len(rx_cod.findall(l.texto)) for l in viz)
        if ctx.ativa("TAG-02") and n_acab < t["acabamentos_minimos"]:
            sem_acab.append((nome, a.bbox))
    _agrupado(ctx, "TAG-01", pag, sem_pd, item="o pé-direito (PD)")
    _agrupado(ctx, "TAG-02", pag, sem_acab)


def _agrupado(ctx, codigo, pag, ocorrencias, **valores):
    """Um comentário por folha, com marca em cada TAG; com um só ambiente, o texto individual."""
    if not ocorrencias:
        return
    (nome, alvo), resto = ocorrencias[0], ocorrencias[1:]
    if not resto:
        ctx.add(codigo, pag.indice, alvo, ambiente=nome, **valores)
        return
    p = ctx.p(codigo)
    nomes = list(dict.fromkeys(n for n, _ in ocorrencias))
    lista = ", ".join(nomes[:p["max_ambientes_listados"]])
    if len(nomes) > p["max_ambientes_listados"]:
        lista += f" e mais {len(nomes) - p['max_ambientes_listados']}"
    ctx.add(codigo, pag.indice, alvo, chave="comentario_agrupado", extras=[b for _, b in resto], ambientes=lista, **valores)
