"""Planta-chave de setorização (PRA-12 a PRA-16): legenda de cores × planta × padrão.

A legenda é lida dos vetores do PDF: amostras preenchidas do mesmo tamanho, cada uma
com o nome do setor à direita. As cores da planta são as dos preenchimentos vetoriais.
"""
from __future__ import annotations

import itertools
import math
import re
from dataclasses import dataclass, field

import fitz

from ..config import normalizar


@dataclass
class Item:
    nome: str
    cor: tuple                 # (r, g, b) 0-255
    amostra: fitz.Rect


@dataclass
class Legenda:
    pagina: int
    itens: list[Item]
    usos: dict = field(default_factory=dict)      # cor -> [Rect] preenchidos fora da legenda

    @property
    def area(self) -> fitz.Rect:
        r = fitz.Rect(self.itens[0].amostra)
        for i in self.itens[1:]:
            r |= i.amostra
        return r


def _hex(c) -> str:
    return "#%02X%02X%02X" % tuple(c)


def _lab(c):
    def f(v):
        v /= 255
        return ((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92
    r, g, b = (f(v) for v in c)
    x = (r * .4124 + g * .3576 + b * .1805) / .95047
    y = r * .2126 + g * .7152 + b * .0722
    z = (r * .0193 + g * .1192 + b * .9505) / 1.08883
    t = lambda v: v ** (1 / 3) if v > 0.008856 else 7.787 * v + 16 / 116
    return 116 * t(y) - 16, 500 * (t(x) - t(y)), 200 * (t(y) - t(z))


def delta_e(a, b) -> float:
    return math.dist(_lab(a), _lab(b))


def _vocabulario(cfg) -> list[str]:
    s = cfg["setorizacao"]
    termos = [x["nome"] for x in s["setores"]] + [i for x in s["setores"] for i in x["inclui"]]
    termos += s["deteccao"]["nomes_extras"]
    return [normalizar(t) for t in termos]


def _preenchidos(desenhos: list, m: fitz.Matrix, canal_min: int):
    """Preenchimentos claros e coloridos (candidatos a setor), já no espaço de exibição."""
    for d in desenhos:
        f = d.get("fill")
        if not f or d.get("type") not in ("f", "fs"):
            continue
        cor = tuple(round(c * 255) for c in f[:3])
        if min(cor) < canal_min or cor == (255, 255, 255):
            continue
        yield cor, d["rect"] * m, d


def detectar(ctx) -> list[Legenda]:
    if hasattr(ctx, "_setorizacao"):
        return ctx._setorizacao
    cfg = ctx.cfg
    det = cfg["setorizacao"]["deteccao"]
    mm = cfg.mm_para_pt
    lado_min, lado_max = (mm(v) for v in det["amostra_lado_mm"])
    vocab = _vocabulario(cfg)
    legendas = []
    for pag in ctx.doc.paginas:
        desenhos, m = ctx.desenhos(pag.indice)
        todos = list(_preenchidos(desenhos, m, det["amostra_canal_min"]))
        amostras = [(cor, r) for cor, r, d in todos
                    if lado_min <= r.width <= lado_max and lado_min <= r.height <= lado_max
                    and max(r.width, r.height) / min(r.width, r.height) <= det["amostra_proporcao_max"]
                    and len(d["items"]) <= 5]
        # agrupa por tamanho: uma legenda usa amostras iguais
        grupos: list[list] = []
        for cor, r in sorted(amostras, key=lambda a: (round(a[1].width), round(a[1].height))):
            g = next((g for g in grupos if abs(g[0][1].width - r.width) <= mm(det["amostra_tolerancia_tamanho_mm"])
                      and abs(g[0][1].height - r.height) <= mm(det["amostra_tolerancia_tamanho_mm"])), None)
            (g.append((cor, r)) if g is not None else grupos.append([(cor, r)]))
        for g in grupos:
            if len(g) < det["amostras_minimas"]:
                continue
            itens = []
            for cor, r in g:
                # texto da mesma linha, à direita, até a próxima amostra dessa linha
                prox = min((o.x0 for _, o in g if o.x0 > r.x1 and abs(o.y0 - r.y0) < r.height / 2),
                           default=r.x1 + mm(det["texto_largura_max_mm"]))
                ls = [l for l in pag.linhas if l.bbox.x0 >= r.x1 - 1 and l.bbox.x0 <= r.x1 + mm(det["texto_distancia_max_mm"])
                      and l.bbox.x0 < prox and abs(l.cy - (r.y0 + r.y1) / 2) < r.height]
                if ls:
                    itens.append(Item(" ".join(l.texto for l in sorted(ls, key=lambda l: l.bbox.x0)).strip(), cor, r))
            if len(itens) < det["amostras_minimas"]:
                continue
            setores = sum(1 for i in itens if any(v in normalizar(i.nome) for v in vocab))
            if setores / len(itens) < det["fracao_nomes_setor"]:
                continue              # legenda de outra coisa (ex.: blocos A/B/C)
            leg = Legenda(pag.indice, sorted(itens, key=lambda i: (i.amostra.x0, i.amostra.y0)))
            amostras_leg = [i.amostra for i in leg.itens]
            for cor, r, _ in todos:
                if not any(r.intersects(a) and abs(r.width - a.width) < 1 for a in amostras_leg):
                    leg.usos.setdefault(cor, []).append(r)
            legendas.append(leg)
    ctx._setorizacao = legendas
    return legendas


def verificar(ctx):
    cfg = ctx.cfg
    if ctx.classe not in cfg["ficha"]["deducao_automatica"]["classes_prancha"]:
        return
    codigos = ("PRA-12", "PRA-13", "PRA-14", "PRA-15", "PRA-16")
    if not any(ctx.ativa(c) for c in codigos):
        return
    legendas = detectar(ctx)
    doc = ctx.doc

    if ctx.ativa("PRA-12") and not legendas:
        geral = any(v.tipo in ("PLANTA_BAIXA", "PLANTA") for p in doc.paginas for v in p.vistas)
        edificacao = any(re.match(ctx.p("PRA-01")["regex_edificacao"], l.texto) for l in doc.todas_linhas())
        if geral and edificacao:
            p0 = doc.paginas[0]
            blocos = [b for b in ctx.blocos[0] if b.nome == "PLANTA-CHAVE"]
            alvo = blocos[0].area if blocos else (p0.carimbo.area if p0.carimbo else fitz.Rect(p0.rect.x1 - 300, 20, p0.rect.x1 - 20, 120))
            ctx.add("PRA-12", 0, fitz.Rect(alvo.x0, alvo.y0, alvo.x1, alvo.y0 + 20))

    padrao = {normalizar(s["nome"]): s for s in cfg["setorizacao"]["setores"]}
    # nome da legenda que não é o do setor, mas um ambiente que ele inclui (COZINHA → OPERAÇÃO)
    # ("ENGENHARIA (se não houver setor próprio)" fica de fora: na legenda, ela é o setor próprio)
    por_ambiente = {normalizar(i): s for s in cfg["setorizacao"]["setores"] for i in s["inclui"] if "(" not in i}
    tol = cfg["setorizacao"]["tolerancia_cor_delta_e"]
    for leg in legendas:
        if ctx.ativa("PRA-14"):
            for i in leg.itens:
                if not leg.usos.get(i.cor):
                    ctx.add("PRA-14", leg.pagina, i.amostra, detalhe=f"\"{i.nome}\" não aparece colorido na planta")
            por_cor: dict = {}
            for i in leg.itens:
                por_cor.setdefault(i.cor, []).append(i)
            for cor, its in por_cor.items():
                if len(its) > 1:
                    ctx.add("PRA-14", leg.pagina, its[1].amostra, extras=[x.amostra for x in its[2:]],
                            detalhe=f"mesma cor ({_hex(cor)}) para {', '.join(x.nome for x in its)}")
        if ctx.ativa("PRA-16"):
            lim = ctx.p("PRA-16")["delta_e_min"]
            pares = [(delta_e(a.cor, b.cor), a, b) for a, b in itertools.combinations(leg.itens, 2) if a.cor != b.cor]
            perto = sorted(p for p in pares if p[0] < lim)
            if perto:
                texto = "; ".join(f"{a.nome} × {b.nome} (ΔE {d:.0f})" for d, a, b in perto[:4])
                if len(perto) > 4:
                    texto += f" e mais {len(perto) - 4} pares"
                ctx.add("PRA-16", leg.pagina, leg.area, regiao=True, pares=texto)
        fora = []
        for i in leg.itens:
            s = padrao.get(normalizar(i.nome))
            if s is None and ctx.ativa("PRA-15"):
                ctx.add("PRA-15", leg.pagina, i.amostra, nome=i.nome, sugestao="um setor da lista padrão")
            s = s or por_ambiente.get(normalizar(i.nome))
            if s is not None and ctx.ativa("PRA-13") and delta_e(i.cor, s["rgb"]) > tol:
                fora.append((i, s))
        if len(fora) == 1:
            i, s = fora[0]
            ctx.add("PRA-13", leg.pagina, i.amostra, nome=i.nome, setor=s["nome"], hex_padrao=s["hex"])
        elif fora:                          # um comentário por legenda, com marca em cada amostra
            setores = "; ".join(f"{i.nome} → {s['hex']}" if normalizar(i.nome) == normalizar(s["nome"])
                                else f"{i.nome} → {s['hex']} ({s['nome']})" for i, s in fora)
            ctx.add("PRA-13", leg.pagina, fora[0][0].amostra, chave="comentario_agrupado",
                    extras=[i.amostra for i, _ in fora[1:]], setores=setores)
