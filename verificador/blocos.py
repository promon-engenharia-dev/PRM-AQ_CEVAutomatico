"""Blocos de texto da folha: título (PLANTA-CHAVE, NOTAS GERAIS, DOCUMENTOS DE REFERÊNCIA…) e corpo."""
from __future__ import annotations

import re
from dataclasses import dataclass

import fitz

from .config import Config, normalizar
from .extracao import dentro
from .modelo import Linha, Pagina


@dataclass
class Bloco:
    nome: str          # chave de PRA-01.blocos_obrigatorios
    titulo: Linha
    corpo: list[Linha]
    area: fitz.Rect


def _eh_titulo(l: Linha, variantes: list[str], cfg: Config) -> bool:
    b = cfg["blocos"]
    if not l.horizontal or l.tamanho < b["tamanho_min_titulo_pt"] or len(l.texto.split()) > b["max_palavras_titulo"]:
        return False
    t = normalizar(l.texto).replace("-", " ")
    return any(t.startswith(normalizar(v).replace("-", " ")) for v in variantes)


def detectar_blocos(pag: Pagina, cfg: Config) -> list[Bloco]:
    b = cfg["blocos"]
    defs = cfg.regra("PRA-01")["blocos_obrigatorios"]
    area_car = pag.carimbo.area if pag.carimbo else None
    blocos = []
    for nome, variantes in defs.items():
        for l in pag.linhas:
            if dentro(l, area_car) or not _eh_titulo(l, variantes, cfg):
                continue
            # borda esquerda: o item "1." logo abaixo do título (blocos numerados); senão, simétrica ao título
            prim = [c for c in pag.linhas if c is not l and 0 <= c.bbox.y0 - l.bbox.y1 <= b["janela_primeiro_item_pt"]
                    and abs(c.cx - l.cx) < b["largura_max_pt"] and re.match(r"^1\s*[.)]?(\s|$)", c.texto)]
            if prim:
                x0 = min(c.bbox.x0 for c in prim) - 5
                x1 = l.cx + (l.cx - x0) + b["margem_direita_pt"]
            else:
                x0, x1 = l.cx - b["meia_largura_padrao_pt"], l.cx + b["meia_largura_padrao_pt"]
            cands = sorted([c for c in pag.linhas if c is not l and c.bbox.y0 > l.bbox.y0 + 1
                            and x0 <= c.bbox.x0 <= x1 and not dentro(c, area_car)], key=lambda c: c.bbox.y0)
            corpo, ultimo = [], l.bbox.y1
            for c in cands:
                if c.bbox.y0 - ultimo > b["gap_fim_pt"]:
                    break
                if any(_eh_titulo(c, v, cfg) for v in defs.values()):
                    break
                corpo.append(c)
                ultimo = max(ultimo, c.bbox.y1)
            area = fitz.Rect(l.bbox)
            for c in corpo:
                area |= c.bbox
            blocos.append(Bloco(nome=nome, titulo=l, corpo=corpo, area=area))
    return blocos
