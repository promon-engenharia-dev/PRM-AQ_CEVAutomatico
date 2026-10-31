"""Reconhecimento do carimbo por modelo (rótulos âncora definidos no regras.json)."""
from __future__ import annotations

import re

import fitz

from .config import Config, normalizar
from .extracao import mesma_linha
from .modelo import Carimbo, CampoCarimbo, Linha, LinhaHistorico, Pagina


def _casa(linha: Linha, rotulo, prefixo: bool) -> bool:
    t = normalizar(linha.texto)
    for r in (rotulo if isinstance(rotulo, list) else [rotulo]):
        r = normalizar(r)
        if (t.startswith(r) if prefixo else t == r):
            return True
    return False


def juntar(linhas: list[Linha]) -> str:
    """Concatena linhas de uma mesma célula; trechos colados (fonte trocada) não ganham espaço."""
    partes, anterior = [], None
    for l in linhas:
        if anterior is not None and partes and mesma_linha(anterior, l) and l.texto == anterior.texto \
                and abs(l.bbox.x0 - anterior.bbox.x0) < 1:
            continue                                   # texto duplicado sobreposto
        if anterior is not None and mesma_linha(anterior, l) and 0 <= l.bbox.x0 - anterior.bbox.x1 < 1.5:
            partes[-1] += l.texto
        elif (anterior is not None and mesma_linha(anterior, l) and anterior.chars
              and sum(1 for _, x1, _c in anterior.chars if x1 > l.bbox.x0 + 0.5) >= 2):
            # texto escrito por cima de outro (ex.: "…AQ4-0004" sob "20004"): vale o que fica visível
            visivel = "".join(c for x0, x1, c in anterior.chars if x1 <= l.bbox.x0 + 0.5).rstrip()
            partes[-1] = (partes[-1][: len(partes[-1]) - len(anterior.texto)] + visivel + l.texto) if partes[-1].endswith(anterior.texto) else visivel + l.texto
        else:
            partes.append(l.texto)
        anterior = l
    return " ".join(partes)


def _cabecalho_historico(linhas, colunas) -> list[tuple[str, Linha]] | None:
    """Linha do cabeçalho do histórico: a primeira coluna com >= 4 colunas na mesma linha."""
    primeira = colunas[0]["rotulo"]
    for cand in linhas:
        if not _casa(cand, primeira, False):
            continue
        achadas = [(colunas[0]["coluna"], cand)]
        for col in colunas[1:]:
            par = next((l for l in linhas if l is not cand and mesma_linha(l, cand) and _casa(l, col["rotulo"], False)), None)
            if par:
                achadas.append((col["coluna"], par))
        if len(achadas) >= 4:
            return achadas
    return None


def _historico(linhas, cab, gap_max) -> list[LinhaHistorico]:
    cab_linhas = [l for _, l in cab]
    topo = min(l.bbox.y0 for l in cab_linhas)
    x0 = min(l.bbox.x0 for l in cab_linhas) - 15
    x1 = max(l.bbox.x1 for l in cab_linhas) + 60
    candidatas = [l for l in linhas if l.bbox.y1 <= topo + 1 and x0 <= l.cx <= x1 and l.horizontal]
    candidatas.sort(key=lambda l: -l.bbox.y0)
    # agrupa em linhas físicas, subindo a partir do cabeçalho
    grupos: list[list[Linha]] = []
    ref = topo
    for l in candidatas:
        if grupos and abs(l.bbox.y0 - grupos[-1][0].bbox.y0) <= 3:
            grupos[-1].append(l)
            continue
        if ref - l.bbox.y1 > gap_max:
            break
        grupos.append([l])
        ref = l.bbox.y0
    centros = [(nome, l.cx) for nome, l in cab]
    resultado = []
    for g in grupos:
        celulas: dict[str, list[Linha]] = {}
        for l in g:
            nome = min(centros, key=lambda c: abs(c[1] - l.cx))[0]
            celulas.setdefault(nome, []).append(l)
        if "revisao" not in celulas:
            break
        resultado.append(LinhaHistorico({n: CampoCarimbo(juntar(sorted(v, key=lambda x: x.bbox.x0)), v)
                                         for n, v in celulas.items()}))
    return resultado             # mais antiga primeiro: as linhas empilham para cima


def reconhecer(pag: Pagina, cfg: Config) -> Carimbo | None:
    ccfg = cfg["carimbo"]
    linhas = pag.linhas
    melhor = None
    for modelo in ccfg["modelos"]:
        n = sum(any(_casa(l, r, True) for l in linhas) for r in modelo["rotulos_identificacao"])
        if n >= modelo["minimo_rotulos"] and (melhor is None or n > melhor[0]):
            melhor = (n, modelo)
    if melhor is None:
        return None
    modelo = melhor[1]

    cab = _cabecalho_historico(linhas, modelo["historico"]["colunas"])
    cab_ids = {id(l) for _, l in cab} if cab else set()

    # rótulos: o escolhido para cada campo + todos os candidatos e delimitadores (servem de fronteira)
    rotulos: dict[str, Linha] = {}
    fronteiras: list[Linha] = [l for _, l in (cab or [])]
    for nome, c in modelo["campos"].items():
        cands = [l for l in linhas if id(l) not in cab_ids and _casa(l, c["rotulo"], c.get("prefixo", False))]
        fronteiras += cands
        if cands:
            rotulos[nome] = max(cands, key=lambda l: (l.bbox.y0, l.bbox.x0))
    for d in modelo.get("rotulos_delimitadores", []):
        fronteiras += [l for l in linhas if _casa(l, d, True)]
    ids_front = {id(l) for l in fronteiras}

    janela = ccfg["janela_valor_pt"]
    regex_data = re.compile(ccfg["regex_data"])
    livres = [l for l in linhas if id(l) not in ids_front and l.horizontal
              and l.tamanho >= ccfg["tamanho_min_valor_pt"]]
    campos: dict[str, CampoCarimbo] = {}
    usados: set[int] = set()
    ordem = sorted(rotulos, key=lambda n: bool(modelo["campos"][n].get("multilinha")))
    for nome in ordem:
        rot = rotulos[nome]
        c = modelo["campos"][nome]
        if c["posicao"] == "abaixo":
            vizinhos = [r for r in fronteiras if r is not rot and mesma_linha(r, rot) and r.bbox.x0 > rot.bbox.x0 + 5]
            limite_x = min((r.bbox.x0 for r in vizinhos), default=rot.bbox.x0 + 400)
            abaixo = [r for r in fronteiras if r.bbox.y0 > rot.bbox.y1 + 1
                      and r.bbox.x0 < limite_x and r.bbox.x1 > rot.bbox.x0]
            limite_y = min((r.bbox.y0 for r in abaixo), default=pag.rect.y1)
            if not c.get("multilinha"):
                limite_y = min(limite_y, rot.bbox.y1 + janela)
            vals = [l for l in livres if id(l) not in usados and l.bbox.y0 >= rot.cy and l.bbox.y0 < limite_y
                    and l.bbox.x0 >= rot.bbox.x0 - 15 and l.bbox.x0 < limite_x]
            vals.sort(key=lambda l: (round(l.bbox.y0), l.bbox.x0))
            if vals and not c.get("multilinha"):
                vals = [v for v in vals if mesma_linha(v, vals[0])]
        else:  # direita
            vals = [l for l in livres if mesma_linha(l, rot) and rot.bbox.x1 < l.bbox.x0 < rot.bbox.x1 + 200]
            vals.sort(key=lambda l: l.bbox.x0)
            datas = [v for v in vals if regex_data.match(v.texto)]
            siglas = [v for v in vals if not regex_data.match(v.texto)]
            if datas:
                campos[nome + "_data"] = CampoCarimbo(datas[0].texto, datas[:1])
            vals = siglas[:1]
        usados |= {id(v) for v in vals}
        campos[nome] = CampoCarimbo(juntar(vals), vals)

    historico = _historico(linhas, cab, ccfg["gap_max_historico_pt"]) if cab else []

    area = None
    for l in fronteiras:
        area = fitz.Rect(l.bbox) if area is None else area | l.bbox
    for c in campos.values():
        for l in c.linhas:
            area |= l.bbox
    for h in historico:
        area |= h.bbox
    area = fitz.Rect(area.x0 - 15, area.y0 - 15, area.x1 + 15, area.y1 + 15) & pag.rect
    return Carimbo(modelo=modelo["nome"], area=area, campos=campos, rotulos=rotulos, historico=historico)
