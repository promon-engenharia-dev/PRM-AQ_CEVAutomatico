"""Leitura do regras.json e utilitários de texto/unidades."""
from __future__ import annotations

import json
import os
import re
import sys
import unicodedata

NOME_ARQUIVO = "regras.json"


def _candidatos():
    # 1) ao lado do executável/script (permite editar sem recompilar)
    if getattr(sys, "frozen", False):
        yield os.path.join(os.path.dirname(sys.executable), NOME_ARQUIVO)
        yield os.path.join(getattr(sys, "_MEIPASS", ""), NOME_ARQUIVO)
    # 2) raiz do projeto
    yield os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), NOME_ARQUIVO)


class Config:
    def __init__(self, caminho: str | None = None, lote_teste: int | None = None):
        if caminho is None:
            caminho = next((c for c in _candidatos() if os.path.isfile(c)), None)
            if caminho is None:
                raise FileNotFoundError(f"{NOME_ARQUIVO} não encontrado")
        self.caminho = caminho
        with open(caminho, encoding="utf-8") as f:
            self.dados = json.load(f)
        self.lote_teste = lote_teste

    def __getitem__(self, chave):
        return self.dados[chave]

    def regra(self, codigo: str) -> dict:
        return self.dados["regras"].get(codigo, {})

    def ativa(self, codigo: str) -> bool:
        r = self.regra(codigo)
        if not r:
            return False
        if self.lote_teste is not None:
            return r.get("lote", 99) <= self.lote_teste
        return bool(r.get("ativa"))

    def comentario(self, _regra: str, _chave: str = "comentario", **valores) -> str:
        modelo = self.regra(_regra)[_chave]
        return modelo.format(**valores)

    # unidades -------------------------------------------------------------
    def altura_mm(self, tamanho_pt: float, fonte: str) -> float:
        u = self.dados["unidades"]
        razoes = u["razao_altura_maiuscula"]
        razao = razoes["padrao"]
        for nome, r in razoes.items():
            if nome != "padrao" and fonte.replace("-", "").replace(",", "").lower().startswith(nome.lower()):
                razao = r
        return tamanho_pt * u["pt_para_mm"] * razao

    def mm_para_pt(self, mm: float) -> float:
        return mm / self.dados["unidades"]["pt_para_mm"]


def sem_acentos(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def normalizar(texto: str, acentos: bool = False) -> str:
    t = re.sub(r"\s+", " ", texto).strip().upper()
    return t if acentos else sem_acentos(t)
