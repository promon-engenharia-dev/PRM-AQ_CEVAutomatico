"""Detecção de tabelas (TABELA DE … / QUADRO DE …) e de títulos de vista."""
from __future__ import annotations

import re
from dataclasses import replace

import fitz

from .config import Config, normalizar
from .extracao import dentro, mesma_linha
from .modelo import Linha, LinhaTabela, Pagina, Tabela, Vista


def _titulos_tabela(pag: Pagina, cfg: Config) -> list[Linha]:
    rx = re.compile(cfg.regra("TAB-01")["regex_titulo_tabela"])
    area_car = pag.carimbo.area if pag.carimbo else None
    return [l for l in pag.linhas if l.horizontal and rx.match(normalizar(l.texto, acentos=True))
            and not dentro(l, area_car)]


def _dono(l: Linha, titulos: list[Linha]) -> Linha | None:
    """Título ao qual a linha mais provavelmente pertence: acima dela, perto em y e sobretudo em x."""
    acima = [t for t in titulos if l.bbox.y0 >= t.bbox.y1 - 1]
    return min(acima, key=lambda t: (l.bbox.y0 - t.bbox.y1) + 2 * abs(t.cx - l.cx)) if acima else None


def _cabecalho(pag: Pagina, titulo: Linha, titulos: list[Linha], janela: float, nomes_tag: set,
               excluir: list) -> list[Linha]:
    """Linha de cabeçalho logo abaixo do título; com cabeçalho em 2 níveis, prefere a linha que tem TAG.
    Cada linha candidata pertence ao título mais próximo dela (tabelas lado a lado)."""
    ids_tit = {id(t) for t in titulos}
    cands = [l for l in pag.linhas if l.horizontal and id(l) not in ids_tit
             and titulo.bbox.y1 - 1 <= l.bbox.y0 <= titulo.bbox.y1 + janela
             and abs(l.cx - titulo.cx) < 350 and not any(dentro(l, a) for a in excluir)]
    cands = [l for l in cands if _dono(l, titulos) is titulo]
    if not cands:
        return []
    tags = [l for l in cands if normalizar(l.texto) in nomes_tag]
    tag = min(tags, key=lambda l: abs(l.cx - titulo.cx) + abs(l.bbox.y0 - titulo.bbox.y1)) if tags else None
    ref = tag or min(cands, key=lambda l: l.bbox.y0)
    linha = sorted([l for l in cands if mesma_linha(l, ref)], key=lambda l: l.bbox.x0)
    if tag is None and any(re.fullmatch(r"[\d.,\s]+(m²|m2|m)?", l.texto) for l in linha):
        return []                  # tabela sem linha de cabeçalho: a 1ª linha já é dado
    return linha


def detectar_tabelas(pag: Pagina, cfg: Config, excluir: list | None = None) -> list[Tabela]:
    p = cfg.regra("KEY-comum")
    tcfg = cfg["tabelas_deteccao"]
    janela = tcfg["janela_cabecalho_pt"]
    gap_fim = tcfg["gap_fim_pt"]
    rx_codigo = re.compile("^" + p["regex_codigo"].replace("\b", "") + "$")
    nomes_tag = {normalizar(x) for x in p["cabecalho_coluna_vocabulario"]}
    titulos = _titulos_tabela(pag, cfg)
    ids_tit = {id(t) for t in titulos}
    excluir = list(excluir or [])
    if pag.carimbo and pag.carimbo.modelo in tcfg["modelos_faixa_lateral_sem_tabelas"]:
        # nesses modelos a faixa vertical do carimbo (notas, legendas, planta-chave) não tem tabelas
        excluir.append(fitz.Rect(pag.carimbo.area.x0, pag.rect.y0, pag.rect.x1, pag.rect.y1))

    brutas = [(t, _cabecalho(pag, t, titulos, janela, nomes_tag, excluir)) for t in titulos]

    # pilhas de tabelas alinhadas (mesma coluna da folha) definem a largura útil
    pilhas: list[list[tuple[Linha, list[Linha]]]] = []
    for t, cab in sorted(brutas, key=lambda x: x[0].bbox.y0):
        for pilha in pilhas:
            if abs(pilha[0][0].cx - t.cx) < tcfg["distancia_pilha_pt"]:
                pilha.append((t, cab))
                break
        else:
            pilhas.append([(t, cab)])

    tabelas = []
    for pilha in pilhas:
        refs = [l for t, cab in pilha for l in ([t] + cab)]
        sx0 = min(l.bbox.x0 for l in refs) - 15
        sx1 = max(l.bbox.x1 for l in refs) + 15
        for t, cab in pilha:
            base = max((l.cy for l in cab), default=t.cy) + 2
            base_y1 = max((l.bbox.y1 for l in cab), default=t.bbox.y1)
            # termina no próximo título abaixo que se sobreponha horizontalmente (de qualquer pilha)
            abaixo = [o.bbox.y0 for o in titulos if o.bbox.y0 > t.bbox.y1 and o.bbox.x1 > sx0 and o.bbox.x0 < sx1]
            limite = min(abaixo, default=pag.rect.y1) - 1
            ids_cab = {id(c) for c in cab}
            corpo = [l for l in pag.linhas if l.horizontal and id(l) not in ids_tit and id(l) not in ids_cab
                     and base < l.cy < limite and sx0 - tcfg["extensao_esquerda_pt"] <= l.bbox.x0 <= sx1
                     and not any(dentro(l, a) for a in excluir)]
            corpo = [l for l in corpo if _dono(l, titulos) is t or _dentro_x(l, cab)]
            corpo.sort(key=lambda l: (l.bbox.y0, l.bbox.x0))
            linhas_ok = []
            ultimo = base_y1
            for l in corpo:
                if l.bbox.y0 - ultimo > gap_fim:
                    break
                linhas_ok.append(l)
                ultimo = max(ultimo, l.bbox.y1)
            col_tag = next((c for c in cab if normalizar(c.texto) in nomes_tag), None)
            registros = _agrupar(linhas_ok, cab, col_tag, rx_codigo)
            area = fitz.Rect(t.bbox)
            for l in cab + linhas_ok:
                area |= l.bbox
            tabelas.append(Tabela(titulo=t, cabecalho=cab, linhas=registros, area=area, pagina=pag.indice))
    return tabelas


def _dentro_x(l: Linha, cab: list[Linha]) -> bool:
    return bool(cab) and min(c.bbox.x0 for c in cab) - 15 <= l.bbox.x0 <= max(c.bbox.x1 for c in cab) + 15


def _agrupar(linhas, cab, col_tag, rx_codigo) -> list[LinhaTabela]:
    regs: list[LinhaTabela] = []
    if col_tag is not None:
        x0, x1 = col_tag.bbox.x0 - 12, col_tag.bbox.x1 + 12
        atual = None
        rx_ini = re.compile(rx_codigo.pattern.rstrip("$") + r"(?=\s|$)")
        for l in linhas:
            m = rx_ini.match(l.texto) if x0 <= l.bbox.x0 <= x1 else None
            if m:
                tag = l if m.end() == len(l.texto) else replace(l, texto=m.group(0))
                atual = LinhaTabela(celulas={"TAG": [tag]}, bbox=fitz.Rect(l.bbox))
                if m.end() < len(l.texto):
                    atual.celulas["DESCRIÇÃO"] = [replace(l, texto=l.texto[m.end():].strip())]
                regs.append(atual)
            elif atual is not None:
                col = _coluna(l, cab)
                atual.celulas.setdefault("DESCRIÇÃO" if col == col_tag.texto else col, []).append(l)
                atual.bbox |= l.bbox
        return regs
    fisicas: list[list[Linha]] = []
    for l in linhas:
        if fisicas and mesma_linha(fisicas[-1][0], l):
            fisicas[-1].append(l)
        else:
            fisicas.append([l])
    for f in fisicas:
        r = LinhaTabela(celulas={}, bbox=fitz.Rect(f[0].bbox))
        for l in sorted(f, key=lambda l: l.bbox.x0):
            r.celulas.setdefault(_coluna(l, cab), []).append(l)
            r.bbox |= l.bbox
        regs.append(r)
    return regs


def _coluna(l: Linha, cab: list[Linha]) -> str:
    """Coluna cujo cabeçalho cobre o centro da linha; se nenhuma, a de borda direita mais próxima."""
    if not cab:
        return "?"
    for c in cab:
        if c.bbox.x0 - 25 <= l.cx <= c.bbox.x1 + 25:
            return c.texto
    return min(cab, key=lambda c: abs(c.bbox.x1 - l.bbox.x1)).texto


def recortar_vistas(pag: Pagina, cfg: Config, excluir: list[fitz.Rect]) -> None:
    """Área de cada vista: acima do título, até o título vizinho à direita e o título de cima.
    (Nos modelos de referência o título fica sob o canto inferior esquerdo do desenho.)"""
    vc = cfg["vistas_recorte"]
    tipos = [(n, re.compile(r)) for n, r in vc["tipos"]]
    vs = [v for v in pag.vistas if not re.match(r"^PLANTA[- ]CHAVE", normalizar(v.titulo.texto, acentos=True))]
    for v in pag.vistas:
        tit = normalizar(v.titulo.texto, acentos=True)
        v.tipo = next((n for n, r in tipos if r.match(tit)), "OUTRA")
    for v in vs:
        t = v.titulo.bbox
        a_direita = [o.titulo.bbox.x0 for o in vs if o is not v and abs(o.titulo.cy - v.titulo.cy) < vc["distancia_mesma_faixa_pt"]
                     and o.titulo.bbox.x0 > t.x0 + 100]
        obst = [x.x0 for x in excluir if x.y0 < t.y0 and x.y1 > t.y0 - 200 and x.x0 > t.x0 + 100]
        direita = min(a_direita + obst + [pag.rect.x1]) - 20
        acima = [o.titulo.bbox.y1 for o in vs if o is not v and o.titulo.bbox.y1 < t.y0 and o.titulo.bbox.x0 < direita
                 and o.titulo.bbox.x0 > t.x0 - vc["alcance_esquerda_titulo_acima_pt"]]
        topo = max(acima + [pag.rect.y0]) + 5
        v.area = fitz.Rect(t.x0 - vc["margem_esquerda_pt"], topo, direita, t.y0 - 1)


def linhas_da_vista(pag: Pagina, v: Vista, excluir: list[fitz.Rect]) -> list[Linha]:
    if v.area is None:
        return []
    return [l for l in pag.linhas if dentro(l, v.area) and not any(dentro(l, x) for x in excluir)]


def detectar_vistas(pag: Pagina, cfg: Config) -> list[Vista]:
    v = cfg.regra("APR-06")["vistas"]
    rx_tit = re.compile(v["regex_titulo"])
    rx_esc = re.compile(v["regex_escala"])
    rx_nivel = re.compile(v["regex_titulo_nivel"])
    dist = cfg.mm_para_pt(v["distancia_escala_mm"])
    area_car = pag.carimbo.area if pag.carimbo else None
    em_tabela = [t.area for t in pag.tabelas]
    vistas = []
    for l in pag.linhas:
        if not (l.horizontal and l.tamanho >= v["tamanho_min_titulo_pt"]):
            continue
        tit = normalizar(l.texto, acentos=True)
        so_nivel = not rx_tit.match(tit) and rx_nivel.match(tit)
        if not (rx_tit.match(tit) or so_nivel) or dentro(l, area_car):
            continue
        if any(dentro(l, a) for a in em_tabela):
            continue
        esc = [e for e in pag.linhas if e is not l and l.cy < e.cy and e.bbox.y0 <= l.bbox.y1 + dist
               and l.bbox.x0 - 20 <= e.bbox.x0 <= l.bbox.x1 and rx_esc.match(normalizar(e.texto, acentos=True))]
        if so_nivel and not esc:
            continue                  # "COBERTURA" solto (ex.: nome de nível) não é título de vista
        vistas.append(Vista(titulo=l, escala=min(esc, key=lambda e: e.bbox.y0) if esc else None, so_nivel=bool(so_nivel)))
    return vistas
