"""Família LD — Documentos de Referência e carimbo contra a Lista de Documentos do projeto."""
from __future__ import annotations

import difflib
import re
from collections import Counter

import fitz

from ..config import normalizar
from ..extracao import mesma_linha
from ..ld import chave, operacao_de


def _tokens(texto: str) -> list[str]:
    """Palavras do título: maiúsculas, com acentos; hífens, barras e pontuação viram separador."""
    return re.sub(r"[^\wÀ-ÿ]+", " ", normalizar(texto, acentos=True)).split()


def _contido(menor: list[str], maior: list[str]) -> bool:
    """As palavras de `menor` aparecem em `maior`, na mesma ordem e em sequência."""
    n = len(menor)
    return n > 0 and any(maior[i:i + n] == menor for i in range(len(maior) - n + 1))


def _diferenca(pdf: list[str], ld: list[str]) -> str:
    """Resumo legível: 'NFRAESTRUTURA → INFRAESTRUTURA; falta: DE TERRAPLENAGEM'."""
    partes = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, pdf, ld).get_opcodes():
        if op == "replace":
            partes.append(f"{' '.join(pdf[i1:i2])} → {' '.join(ld[j1:j2])}")
        elif op == "delete":
            partes.append(f"sobra: {' '.join(pdf[i1:i2])}")
        elif op == "insert":
            partes.append(f"falta: {' '.join(ld[j1:j2])}")
    return "; ".join(partes)


def _operacao_da_ld(ld) -> str:
    c = Counter(operacao_de(d.promon) for d in ld.docs)
    c.pop("", None)
    return c.most_common(1)[0][0] if c else ""


def _sugestao(codigo: str, ld, corte: float) -> str | None:
    k = chave(codigo)
    cands = difflib.get_close_matches(k, list(ld.indice), n=1, cutoff=corte)
    return cands[0] if cands else None


def _itens(bloco, rx_cod):
    """[(linha_do_código, código, título)] — o título continua nas linhas logo abaixo, até o próximo código."""
    corpo = sorted(bloco.corpo, key=lambda l: (round(l.bbox.y0), l.bbox.x0))
    itens = []
    for i, l in enumerate(corpo):
        m = rx_cod.search(l.texto)
        if not m:
            continue
        resto = [l.texto[m.end():]]
        resto += [o.texto for o in corpo if o is not l and mesma_linha(o, l) and o.bbox.x0 > l.bbox.x1 - 1]
        ultimo = l
        for o in corpo[i + 1:]:
            if rx_cod.search(o.texto) or re.match(r"^\s*\d{1,2}\s*[.)\-]?\s*$", o.texto):
                break
            if 0 <= o.bbox.y0 - ultimo.bbox.y1 <= 6 and o.bbox.x0 >= l.bbox.x0 - 5 and not mesma_linha(o, l):
                resto.append(o.texto)
                ultimo = o
        titulo = re.sub(r"^[\s\-–|:]+", "", " ".join(resto)).strip()
        itens.append((l, m.group(0), titulo))
    return itens


def verificar(ctx):
    ld = getattr(ctx, "ld", None)
    if ld is None:
        return
    p = ctx.p("LD-comum")
    rx_cod = re.compile(p["regex_codigo"])
    op_ld = _operacao_da_ld(ld)

    # LD-04 / LD-05: carimbo ------------------------------------------------------
    for pag in ctx.doc.paginas:
        car = pag.carimbo
        if not car:
            continue
        num = car.campos.get("numero_documento")
        promon = car.campos.get("numero_promon")
        op_doc = operacao_de(promon.valor if promon else "", num.valor if num else "")
        if op_doc and op_ld and op_doc != op_ld:
            if ctx.ativa("LD-00"):
                ctx.add("LD-00", pag.indice, car.area, op_doc=op_doc, op_ld=op_ld)
            return                          # LD de outra operação: não compara nada
        doc_ld = None
        for campo in (num, promon):
            if campo and campo.valor:
                doc_ld = doc_ld or ld.busca(campo.valor)
        if num and num.valor and doc_ld is None and ctx.ativa("LD-04"):
            ctx.add("LD-04", pag.indice, num.bbox if num.linhas else car.area, numero=num.valor)
        tit = car.campos.get("titulo")
        if doc_ld and tit and tit.valor and ctx.ativa("LD-05"):
            if not _contido(_tokens(doc_ld.titulo), _tokens(tit.valor)):
                ctx.add("LD-05", pag.indice, tit.bbox if tit.linhas else car.area, regiao=True, titulo_ld=doc_ld.titulo,
                        diferenca=_diferenca(_tokens(tit.valor), _tokens(doc_ld.titulo)))

    # LD-01 / LD-02 / LD-03: lista de Documentos de Referência --------------------
    for pag in ctx.doc.paginas:
        for b in ctx.blocos[pag.indice]:
            if b.nome != "DOCUMENTOS DE REFERÊNCIA":
                continue
            for l, cod, titulo in _itens(b, rx_cod):
                d = ld.busca(cod)
                if d is None:
                    if ctx.ativa("LD-01"):
                        s = _sugestao(cod, ld, p["similaridade_sugestao"])
                        if s:
                            ctx.add("LD-01", pag.indice, l.bbox, chave="comentario_sugestao", codigo=cod,
                                    sugestao=ld.indice[s].cliente if chave(ld.indice[s].cliente) == s else ld.indice[s].promon,
                                    titulo_ld=ld.indice[s].titulo)
                        else:
                            ctx.add("LD-01", pag.indice, l.bbox, codigo=cod)
                    continue
                if d.acao == "E" and ctx.ativa("LD-03"):
                    ctx.add("LD-03", pag.indice, l.bbox, codigo=cod)
                if titulo and ctx.ativa("LD-02") and _tokens(titulo) != _tokens(d.titulo):
                    ctx.add("LD-02", pag.indice, l.bbox, codigo=cod, titulo_ld=d.titulo,
                            diferenca=_diferenca(_tokens(titulo), _tokens(d.titulo)))
