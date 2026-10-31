"""Extração do texto da página no espaço de exibição, com filtros.

Remove o que não pertence ao documento original: comentários de CEVs
anteriores achatados no conteúdo (texto nas cores de verificação), carimbo
"Cópia de Verificação", assinatura digital e texto oculto minúsculo.
"""
from __future__ import annotations

import os
import re

import fitz

from .config import Config
from .modelo import Documento, Linha, Pagina


def _cor_rgb(c: int) -> tuple[int, int, int]:
    return (c >> 16) & 255, (c >> 8) & 255, c & 255


def _cor_proxima(c: int, alvo: str, tol: int) -> bool:
    a = int(alvo, 16)
    return all(abs(x - y) <= tol for x, y in zip(_cor_rgb(c), _cor_rgb(a)))


class FiltroConteudo:
    def __init__(self, cfg: Config):
        f = cfg["filtros"]["conteudo"]
        self.regex = [re.compile(r) for r in f["regex_texto_ignorar"]]
        self.fontes = set(f["fontes_ignorar"])
        self.cores = f["cores_ignorar"]
        self.tol = f["tolerancia_cor"]
        self.tam_min = f["tamanho_min_pt"]

    def ignorar(self, texto: str, fonte: str, tamanho: float, cor: int) -> bool:
        if tamanho < self.tam_min:
            return True
        if fonte in self.fontes:
            return True
        if any(_cor_proxima(cor, c, self.tol) for c in self.cores):
            return True
        return any(r.search(texto) for r in self.regex)


def _vetor_horizontal(direcao, m: fitz.Matrix) -> bool:
    p0 = fitz.Point(0, 0) * m
    p1 = fitz.Point(direcao) * m
    return abs((p1 - p0).y) < 0.1


def extrair_pagina(page: fitz.Page, filtro: FiltroConteudo) -> Pagina:
    m = page.rotation_matrix
    pag = Pagina(indice=page.number, rect=fitz.Rect(page.rect), rotacao=page.rotation)
    # sem MEDIABOX_CLIP: texto que atravessa a borda precisa aparecer inteiro (APR-05)
    dados = page.get_text("rawdict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
    for bloco in dados["blocks"]:
        if bloco["type"] != 0:
            continue
        for ln in bloco["lines"]:
            for s in ln["spans"]:
                s["text"] = "".join(c["c"] for c in s["chars"])
            spans = [s for s in ln["spans"] if s["text"].strip()]
            if not spans:
                continue
            texto = re.sub(r"\s+", " ", "".join(s["text"] for s in ln["spans"])).strip()
            chars = []
            for s in ln["spans"]:
                for c in s["chars"]:
                    r = fitz.Rect(c["bbox"]) * m
                    chars.append((r.x0, r.x1, c["c"]))
            principal = max(spans, key=lambda s: len(s["text"].strip()))
            if filtro.ignorar(texto, principal["font"], principal["size"], principal["color"]):
                continue
            bbox = fitz.Rect(ln["bbox"]) * m
            if not bbox.intersects(pag.rect):
                continue                      # inteiramente fora da folha: invisível
            pag.linhas.append(Linha(
                texto=texto,
                bbox=bbox,
                fonte=principal["font"],
                tamanho=principal["size"],
                cor=principal["color"],
                flags=principal["flags"],
                horizontal=_vetor_horizontal(ln["dir"], m),
                pagina=page.number,
                chars=chars,
            ))
    return pag


def extrair_documento(caminho: str, cfg: Config) -> Documento:
    filtro = FiltroConteudo(cfg)
    with fitz.open(caminho) as doc:
        paginas = [extrair_pagina(p, filtro) for p in doc]
    base = os.path.splitext(os.path.basename(caminho))[0]
    return Documento(caminho=caminho, paginas=paginas, nome_base=base)


# utilitários geométricos ---------------------------------------------------

def mesma_linha(a: Linha, b: Linha, tol: float = 3.0) -> bool:
    return abs(a.bbox.y0 - b.bbox.y0) <= tol or abs(a.cy - b.cy) <= tol


def dentro(l: Linha, r: fitz.Rect | None) -> bool:
    return r is not None and r.contains(fitz.Point(l.cx, l.cy))
