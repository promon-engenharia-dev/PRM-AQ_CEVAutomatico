"""Linha de comando: verificador [opções] arquivo1.pdf [arquivo2.pdf ...]

Sem arquivos (ou com --janela) abre a janela da ferramenta.
"""
from __future__ import annotations

import argparse
import os
import sys
import traceback
from collections import Counter

from . import ficha as fichas
from . import nucleo
from .config import Config
from .nucleo import caminho_saida  # noqa: F401  (usado pelo validador)


def processar(pdf: str, cfg: Config, args) -> tuple[str, list]:
    op = nucleo.Opcoes(ficha=args.ficha, sem_ficha=args.sem_ficha, ld=args.ld, sem_ld=args.sem_ld, saida=args.saida,
                       gerar_csv=args.csv, gerar_html=args.html, revisao=args.revisao)
    pre = nucleo.preparar(pdf, cfg, op)
    for a in pre.avisos:
        print("   aviso:", a, file=sys.stderr)
    ficha = None
    if args.ficha:
        ficha = fichas.deduzir(pdf, cfg, pre.existente)
    elif not args.sem_ficha:
        ficha = fichas.obter(pdf, cfg, formulario=not args.sem_formulario, sugestao=pre.sugestao)
    res = nucleo.finalizar(pre, ficha, cfg, op)
    if res.caminho_ld:
        print(f"   LD: {os.path.basename(res.caminho_ld)}")
    return res.saida, res.achados


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="verificador", description="Verificação automática de apresentação (CEV) — processamento 100% local.")
    ap.add_argument("pdfs", nargs="*", help="arquivos PDF")
    ap.add_argument("--janela", action="store_true", help="abre a janela da ferramenta (com os PDFs indicados já na lista)")
    ap.add_argument("--ficha", help="usar esta ficha JSON (em vez de <arquivo>.ficha.json)")
    ap.add_argument("--sem-ficha", action="store_true", help="não usar ficha (regras de comparação com a ficha não rodam)")
    ap.add_argument("--sem-formulario", action="store_true", help="não abrir o formulário; usa a ficha existente, se houver")
    ap.add_argument("--lote", type=int, help="TESTE: ativa todas as regras até este lote, ignorando 'ativa' do regras.json")
    ap.add_argument("--saida", help="pasta de saída (padrão: a do PDF)")
    ap.add_argument("--ld", help="Lista de Documentos do projeto (.xlsx)")
    ap.add_argument("--sem-ld", action="store_true", help="não procurar nem usar LD")
    ap.add_argument("--csv", dest="csv", action="store_true", default=None, help="grava também a lista de achados em CSV")
    ap.add_argument("--sem-csv", dest="csv", action="store_false", help="não grava o CSV")
    ap.add_argument("--html", dest="html", action="store_true", default=None, help="grava o relatório HTML")
    ap.add_argument("--sem-html", dest="html", action="store_false", help="não grava o relatório HTML")
    ap.add_argument("--revisao", help="versão Claude: acrescenta os achados da revisão assistida (<arquivo>.revisao.json)")
    ap.add_argument("--regras", help="caminho alternativo do regras.json")
    ap.add_argument("--ajuda-ficha", action="store_true", help="explica cada campo da ficha")
    args = ap.parse_args(argv)

    cfg = Config(args.regras, lote_teste=args.lote)
    if args.ajuda_ficha:
        print(fichas.ajuda_texto(cfg))
        return 0
    if args.janela or not args.pdfs:
        try:
            from .interface_web import abrir          # janela HTML (WebView2)
        except ImportError:
            from .interface import abrir              # reserva: janela Tkinter
        try:
            return abrir(cfg, args.pdfs)
        except Exception as e:                         # WebView2 ausente ou bloqueado: cai para Tkinter
            print(f"Janela HTML indisponível ({e}); abrindo a janela simples.", file=sys.stderr)
            from .interface import abrir as abrir_tk
            return abrir_tk(cfg, args.pdfs)
    erros = 0
    for pdf in args.pdfs:
        try:
            saida, achados = processar(pdf, cfg, args)
            sev = Counter(a.severidade for a in achados)
            print(f"{os.path.basename(pdf)} -> {os.path.basename(saida)}: {len(achados)} achado(s) "
                  f"({sev.get('ERRO', 0)} ERRO, {sev.get('ATENCAO', 0)} ATENÇÃO"
                  + (f", {sev['CORRETO']} CORRETO)" if sev.get("CORRETO") else ")"))
        except PermissionError as e:
            erros += 1
            print(f"{os.path.basename(pdf)}: FALHOU — não consegui gravar {e.filename}. "
                  f"O arquivo de saída está aberto em outro programa? Feche-o e rode de novo.", file=sys.stderr)
        except Exception as e:  # um arquivo com problema não interrompe os demais
            erros += 1
            print(f"{os.path.basename(pdf)}: FALHOU — {e}", file=sys.stderr)
            traceback.print_exc()
    return 1 if erros else 0
