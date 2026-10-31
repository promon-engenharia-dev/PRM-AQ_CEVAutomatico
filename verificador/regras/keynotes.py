"""Família D — cruzamento tabela × desenho (KEY)."""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from ..config import normalizar
from ..extracao import dentro


@dataclass
class Analise:
    vocabulario: dict = field(default_factory=dict)   # código -> [(tabela, linha_tabela)]
    prefixo_tabela: dict = field(default_factory=dict)  # prefixo -> nome da tabela
    usos: dict = field(default_factory=dict)          # código -> [(pagina, Linha)]


def _excluido_contexto(texto: str, ini: int, fim: int, rxs) -> bool:
    janela = texto[max(0, ini - 15): fim + 15]
    return any(r.search(janela) for r in rxs)


def analisar(ctx) -> Analise:
    if getattr(ctx, "_keynotes", None):
        return ctx._keynotes
    p = ctx.p("KEY-comum")
    rx = re.compile(p["regex_codigo"])
    exc = p["exclusoes"]
    pref_exc = set(exc["prefixos"])
    cod_exc = set(exc["codigos"])
    rx_ctx = [re.compile(r) for r in exc["regex_contexto"]]
    a = Analise()
    for pag in ctx.doc.paginas:
        for t in pag.tabelas:
            regs = [(reg, rx.fullmatch(reg.texto("TAG"))) for reg in t.linhas]
            regs = [(reg, m) for reg, m in regs if m]
            cont = Counter(m.group("prefixo") for _, m in regs)
            if not cont:
                continue
            topo = cont.most_common(1)[0][1]
            dominantes = {pr for pr, n in cont.items() if n >= max(1, p["fracao_prefixo_dominante"] * topo)}
            for reg, m in regs:
                if m.group("prefixo") not in dominantes:
                    continue            # linha vazada de outra tabela vizinha
                a.vocabulario.setdefault(m.group(0), []).append((t, reg))
                a.prefixo_tabela.setdefault(m.group("prefixo"), t.nome)
    for pag in ctx.doc.paginas:
        areas = [t.area for t in pag.tabelas] + ([pag.carimbo.area] if pag.carimbo else [])
        areas += [b.area for b in ctx.blocos[pag.indice]]
        for l in pag.linhas:
            if any(dentro(l, ar) for ar in areas):
                continue
            for m in rx.finditer(l.texto):
                cod, pre = m.group(0), m.group("prefixo")
                if pre in pref_exc or cod in cod_exc or _excluido_contexto(l.texto, m.start(), m.end(), rx_ctx):
                    continue
                a.usos.setdefault(cod, []).append((pag.indice, l))
    ctx._keynotes = a
    return a


def verificar(ctx):
    p = ctx.p("KEY-comum")
    a = analisar(ctx)
    eh_prancha = ctx.classe in ctx.cfg["ficha"]["deducao_automatica"]["classes_prancha"]
    if not eh_prancha:
        return
    if len(a.vocabulario) < p["vocabulario_minimo"]:
        tem_col_tag = any(t.linhas and "TAG" in t.linhas[0].celulas for pg in ctx.doc.paginas for t in pg.tabelas)
        if ctx.ativa("KEY-00") and a.usos and tem_col_tag:
            pag, l = next(iter(a.usos.values()))[0]
            ctx.add("KEY-00", pag, l.bbox)
        return
    pre_rx = re.compile(p["regex_codigo"])
    if ctx.ativa("KEY-01") or ctx.ativa("KEY-02"):
        for cod, ocs in sorted(a.usos.items()):
            if cod in a.vocabulario:
                continue
            pre = pre_rx.fullmatch(cod).group("prefixo")
            por_pag = {}
            for pag, l in ocs:
                por_pag.setdefault(pag, []).append(l)
            for pag, ls in por_pag.items():
                extras = [x.bbox for x in ls[1:]]
                if pre in a.prefixo_tabela and ctx.ativa("KEY-01"):
                    ctx.add("KEY-01", pag, ls[0].bbox, extras=extras, codigo=cod, tabela_do_prefixo=a.prefixo_tabela[pre])
                elif pre not in a.prefixo_tabela and ctx.ativa("KEY-02"):
                    ctx.add("KEY-02", pag, ls[0].bbox, extras=extras, codigo=cod)
    if ctx.ativa("KEY-03"):
        sem_tag = set(p["prefixos_sem_tag_no_desenho"])
        for cod, regs in a.vocabulario.items():
            if cod not in a.usos and pre_rx.fullmatch(cod).group("prefixo") not in sem_tag:
                t, reg = regs[0]
                ctx.add("KEY-03", t.pagina, reg.bbox, codigo=cod, tabela=t.nome)
    if ctx.ativa("KEY-04"):
        for cod, regs in a.vocabulario.items():
            descs = {}
            for t, reg in regs:
                d = " ".join(v.texto for k, ls in reg.celulas.items() if k != "TAG"
                             for v in ls if not re.fullmatch(r"[\d.,\s]+(m²|m2|m|un)?", v.texto))
                d = re.sub(r"[.;\s]+$", "", normalizar(d, acentos=True))
                if d:
                    descs.setdefault(d, (t, reg))
            lim = p["similaridade_max_descricoes"]
            itens = list(descs.items())
            par = next(((x, y) for i, x in enumerate(itens) for y in itens[i + 1:]
                        if not (x[0] in y[0] or y[0] in x[0]) and SequenceMatcher(None, x[0], y[0]).ratio() < lim), None)
            if par:
                (d1, _), (d2, (t2, reg2)) = par
                ctx.add("KEY-04", t2.pagina, reg2.bbox, regiao=True, codigo=cod, desc1=d1[:60], desc2=d2[:60])
