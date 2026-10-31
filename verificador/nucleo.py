"""Fluxo de verificação de um PDF, comum à linha de comando e à janela.

preparar()  — lê o PDF, reconhece o carimbo, acha e lê a LD, monta a sugestão de ficha (sem interação);
finalizar() — roda as regras com a ficha escolhida e grava o _CEV.pdf, o CSV e o relatório HTML.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

from . import ficha as fichas
from . import ld as ld_mod
from .anotador import anotar, numerar
from .carimbo import reconhecer
from .config import Config
from .extracao import extrair_documento
from .modelo import Achado, Documento
from .regras import executar
from .regras.carimbo import numero_do_arquivo
from .relatorio import gravar_csv, gravar_html

_LDS: dict[str, object] = {}


@dataclass
class Opcoes:
    ficha: str | None = None          # caminho de ficha explícita
    sem_ficha: bool = False
    ld: str | None = None             # caminho de LD explícita
    sem_ld: bool = False
    saida: str | None = None          # pasta de saída (padrão: a do PDF)
    gerar_csv: bool | None = None     # None = padrão de regras.json → saidas
    gerar_html: bool | None = None
    revisao: str | None = None        # achados da revisão assistida (versão Claude), <arquivo>.revisao.json


@dataclass
class Preparo:
    pdf: str
    doc: Documento
    operacao: str
    existente: dict
    caminho_ld: str | None
    ld: object | None
    sugestao: dict
    avisos: list[str] = field(default_factory=list)


@dataclass
class Resultado:
    pdf: str
    saida: str
    csv: str
    html: str
    achados: list[Achado]
    caminho_ld: str | None


def carregar_ld(caminho: str | None, cfg: Config, avisos: list | None = None):
    if not caminho:
        return None
    if caminho not in _LDS:
        try:
            _LDS[caminho] = ld_mod.ler(caminho, cfg)
        except Exception as e:
            if avisos is not None:
                avisos.append(f"Não consegui ler a LD {os.path.basename(caminho)}: {e}")
            _LDS[caminho] = None
    return _LDS[caminho]


def caminho_saida(pdf: str, cfg: Config, pasta: str | None) -> str:
    nc = cfg["nome_arquivo"]
    base = os.path.splitext(os.path.basename(pdf))[0]
    base += nc["sufixo_saida_se_ja_cev"] if re.search(nc["regex_ja_e_cev"], base) else nc["sufixo_saida"]
    return os.path.join(pasta or os.path.dirname(os.path.abspath(pdf)), base + ".pdf")


def preparar(pdf: str, cfg: Config, op: Opcoes) -> Preparo:
    doc = extrair_documento(pdf, cfg)
    car = reconhecer(doc.paginas[0], cfg) if doc.paginas else None
    campos = {k: c.valor for k, c in (car.campos.items() if car else [])}
    numero = numero_do_arquivo(doc.nome_base)
    operacao = ld_mod.operacao_de(campos.get("numero_promon", ""), campos.get("numero_documento", ""), numero)
    existente = fichas.ler(op.ficha or fichas.caminho_ficha(pdf, cfg)) or {}
    caminho_ld = op.ld or (None if op.sem_ld else ld_mod.localizar(pdf, cfg, existente, operacao))
    avisos: list[str] = []
    ld = carregar_ld(caminho_ld, cfg, avisos)
    sugestao = {"ld": caminho_ld or "", "numero_documento": numero}
    if ld:
        d = ld.busca(numero) or ld.busca(campos.get("numero_documento", ""))
        if d:
            sugestao["titulo"] = d.titulo
    return Preparo(pdf, doc, operacao, existente, caminho_ld, ld, sugestao, avisos)


def ficha_inicial(pre: Preparo, cfg: Config) -> dict:
    """Valores com que o formulário abre: ficha salva → revisão anterior → LD/nome do arquivo."""
    base = dict(pre.existente or fichas.ficha_anterior(pre.pdf, cfg) or {})
    for k, v in pre.sugestao.items():
        if v and not base.get(k):
            base[k] = v
    return fichas.deduzir(pre.pdf, cfg, base)


def finalizar(pre: Preparo, ficha: dict | None, cfg: Config, op: Opcoes) -> Resultado:
    caminho_ld, ld = pre.caminho_ld, pre.ld
    if ficha and ficha.get("ld") and ficha["ld"] != caminho_ld and not op.ld:
        caminho_ld = ficha["ld"]
        ld = carregar_ld(caminho_ld, cfg, pre.avisos)
    if ld and pre.operacao:
        ld_mod.lembrar(pre.operacao, caminho_ld)
    achados = executar(pre.doc, cfg, ficha, ld)
    if op.revisao:
        from .revisao import carregar
        achados += carregar(op.revisao, pre.doc, cfg, pre.avisos)
    achados = numerar(achados)
    saida = caminho_saida(pre.pdf, cfg, op.saida)
    if op.saida:
        os.makedirs(op.saida, exist_ok=True)
    anotar(pre.pdf, saida, [a for a in achados if a.severidade != "CORRETO"], cfg, {p.indice: [l.bbox for l in p.linhas] for p in pre.doc.paginas})
    base = os.path.splitext(saida)[0]
    padrao = cfg["saidas"]
    csv_ = html = ""
    if padrao["csv"] if op.gerar_csv is None else op.gerar_csv:
        csv_ = base + ".csv"
        gravar_csv(csv_, os.path.basename(pre.pdf), achados, cfg)
    if padrao["html"] if op.gerar_html is None else op.gerar_html:
        html = base + ".html"
        gravar_html(html, pre.pdf, saida, achados, cfg, caminho_ld if ld else None)
    return Resultado(pre.pdf, saida, csv_, html, achados, caminho_ld if ld else None)
