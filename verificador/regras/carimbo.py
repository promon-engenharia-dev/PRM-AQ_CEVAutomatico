"""Família B — carimbo (CAR)."""
from __future__ import annotations

import re
from datetime import datetime
from difflib import SequenceMatcher

import fitz

from ..config import normalizar, sem_acentos
from ..modelo import Carimbo, Pagina


def _alvo(car: Carimbo, campo: str) -> fitz.Rect:
    c = car.campos.get(campo)
    if c and c.linhas:
        return c.bbox
    if campo in car.rotulos:
        return car.rotulos[campo].bbox
    return car.area


def _comparavel(v: str) -> str:
    return re.sub(r"\s+", "", normalizar(v, acentos=True))


def revisao_do_arquivo(nome_base: str, cfg) -> str | None:
    for rx in cfg["nome_arquivo"]["regex_revisao"]:
        m = re.search(rx, nome_base)
        if m:
            return m.group("rev")
    return None


def numero_do_arquivo(nome_base: str) -> str:
    base = re.sub(r"(_CEV\d*)?(_auto)?$", "", nome_base)
    return re.sub(r"_R?[0-9A-Z]{1,3}$", "", base)


def _data(v: str):
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(v.strip(), fmt)
        except ValueError:
            pass
    return None


def _sucessora(a: str, b: str) -> bool | None:
    """True/False quando dá para julgar; None para revisões fora dos esquemas simples."""
    if a.isdigit() and b.isdigit():
        return int(b) == int(a) + 1
    if a == "0" and b == "A":
        return True
    if len(a) == 1 and len(b) == 1 and a.isalpha() and b.isalpha():
        return ord(b) == ord(a) + 1
    return None


def verificar(ctx):
    cfg = ctx.cfg
    eh_prancha = ctx.classe in cfg["ficha"]["deducao_automatica"]["classes_prancha"]
    sem_carimbo = [p.indice for p in ctx.doc.paginas if p.carimbo is None]
    if sem_carimbo and eh_prancha and ctx.ativa("CAR-00"):
        p0 = ctx.doc.paginas[sem_carimbo[0]]
        ctx.add("CAR-00", p0.indice, fitz.Rect(p0.rect.x1 - 300, p0.rect.y1 - 150, p0.rect.x1 - 20, p0.rect.y1 - 20))
    rev_arquivo = revisao_do_arquivo(ctx.doc.nome_base, cfg)
    for pag in ctx.doc.paginas:
        if pag.carimbo:
            _pagina(ctx, pag, pag.carimbo, rev_arquivo)


def _pagina(ctx, pag: Pagina, car: Carimbo, rev_arquivo):
    cfg = ctx.cfg
    v = {k: c.valor for k, c in car.campos.items()}
    hist = car.historico
    ultima = hist[-1] if hist else None

    if ctx.ativa("CAR-01"):
        for campo in cfg["carimbo"]["campos_obrigatorios"]:
            if campo in car.rotulos and not v.get(campo, "").strip():
                ctx.add("CAR-01", pag.indice, car.rotulos[campo].bbox, campo=_nome_campo(campo))
        if ultima:
            for col in cfg["carimbo"]["colunas_obrigatorias_ultima_revisao"]:
                if not ultima.valor(col).strip():
                    ctx.add("CAR-01", pag.indice, ultima.bbox, regiao=True, chave="comentario_historico",
                            coluna=_nome_campo(col), rev=ultima.valor("revisao"))

    if not hist and ctx.ativa("CAR-00"):
        ctx.add("CAR-00", pag.indice, car.area, chave="comentario_historico")

    num_car = v.get("numero_documento", "").strip()
    num_arq = numero_do_arquivo(ctx.doc.nome_base)
    if ctx.ativa("CAR-03") and num_car and num_arq and _comparavel(num_car) != _comparavel(num_arq):
        ctx.add("CAR-03", pag.indice, _alvo(car, "numero_documento"), chave="comentario_numero",
                numero_carimbo=num_car, numero_arquivo=num_arq)

    rev_car = v.get("revisao", "").strip()
    if ctx.ativa("CAR-03") and rev_arquivo and rev_car and _comparavel(rev_car) != _comparavel(rev_arquivo):
        ctx.add("CAR-03", pag.indice, _alvo(car, "revisao"), rev_carimbo=rev_car, rev_arquivo=rev_arquivo)

    if ctx.ativa("CAR-04") and ultima and rev_car and _comparavel(rev_car) != _comparavel(ultima.valor("revisao")):
        ctx.add("CAR-04", pag.indice, _alvo(car, "revisao"), rev_carimbo=rev_car, rev_historico=ultima.valor("revisao"))

    if ctx.ativa("CAR-05"):
        for a, b in zip(hist, hist[1:]):
            ra, rb = a.valor("revisao").strip(), b.valor("revisao").strip()
            ok = _sucessora(ra, rb)
            if ok is False:
                ctx.add("CAR-05", pag.indice, b.bbox, regiao=True, detalhe=f"revisão {ra} seguida de {rb}")
            da, db = _data(a.valor("data")), _data(b.valor("data"))
            if da and db and db < da:
                ctx.add("CAR-05", pag.indice, b.bbox, regiao=True,
                        detalhe=f"data da revisão {rb} ({b.valor('data')}) anterior à da revisão {ra} ({a.valor('data')})")

    if ctx.ativa("CAR-06"):
        revs = [h.valor("revisao").strip() for h in hist]
        tem_num = any(r.isdigit() and r != "0" for r in revs)
        tem_alfa = any(r.isalpha() for r in revs)
        esquema = ctx.ficha.get("esquema_revisao")
        if tem_num and tem_alfa:
            ctx.add("CAR-06", pag.indice, hist[-1].bbox, regiao=True, rev=", ".join(revs), esquema="único")
        elif esquema and rev_car and rev_car != "0":
            if (esquema == "alfabetico" and rev_car.isdigit()) or (esquema == "numerico" and rev_car.isalpha()):
                ctx.add("CAR-06", pag.indice, _alvo(car, "revisao"), rev=rev_car, esquema=esquema)

    if ctx.ativa("CAR-07"):
        p = ctx.p("CAR-07")
        alvo_txt = cfg["revisao"]["descricao_rev0"]
        alvo_n = sem_acentos(alvo_txt)
        for i, h in enumerate(hist):
            desc = normalizar(h.valor("descricao"), acentos=True)
            desc_n = sem_acentos(desc)
            parecido = SequenceMatcher(None, desc_n, alvo_n).ratio() >= p["similaridade_grafia"]
            cel = h.celulas.get("descricao")
            alvo = cel.bbox if cel else h.bbox
            if parecido and desc != alvo_txt:
                ctx.add("CAR-07", pag.indice, alvo, chave="comentario_grafia", valor=h.valor("descricao"))
            elif desc == alvo_txt and i > 0:
                ctx.add("CAR-07", pag.indice, alvo, rev=h.valor("revisao"))
            elif i == 0 and h.valor("revisao").strip() == "0" and desc and not parecido:
                ctx.add("CAR-07", pag.indice, alvo, chave="comentario_rev0", rev="0")

    if ctx.ativa("CAR-09") and v.get("arquivo_magnetico"):
        valor = v["arquivo_magnetico"]
        m = re.match(cfg["carimbo"]["arquivo_magnetico"]["regex"], re.sub(r"\s+", "", valor), re.I)
        num, rev = v.get("numero_documento", ""), rev_car
        if not m or (num and _comparavel(m.group("numero")) != _comparavel(num)) \
                or (rev and _comparavel(m.group("rev")) != _comparavel(rev)):
            ctx.add("CAR-09", pag.indice, _alvo(car, "arquivo_magnetico"), valor=valor, numero=num or "?", rev=rev or "?")

    if ctx.ativa("CAR-10") and ultima:
        ex, ve = ultima.valor("executado").strip(), ultima.valor("verificado").strip()
        if ex and ex == ve:
            ctx.add("CAR-10", pag.indice, ultima.bbox, regiao=True)

    if ctx.ativa("CAR-02") and ctx.ficha:
        _comparar_ficha(ctx, pag, car, v, ultima)


_NOMES = {
    "numero_documento": "Número do documento", "revisao": "Revisão", "folha": "Folha", "escala": "Escala",
    "titulo": "Título", "descricao": "Descrição da revisão", "data": "Data", "executado": "Executado",
    "verificado": "Verificado", "aprovado": "Aprovado", "cliente_operacao": "Cliente/operação",
    "descricao_revisao": "Descrição da revisão", "total_folhas": "Total de folhas",
}


def _nome_campo(c: str) -> str:
    return _NOMES.get(c, c)


def _comparar_ficha(ctx, pag, car, v, ultima):
    f = ctx.ficha
    pares = {
        "numero_documento": (v.get("numero_documento"), _alvo(car, "numero_documento")),
        "revisao": (v.get("revisao"), _alvo(car, "revisao")),
        "titulo": (v.get("titulo"), _alvo(car, "titulo")),
        "cliente_operacao": (v.get("cliente_operacao"), _alvo(car, "cliente_operacao")),
    }
    if ultima:
        for col, chave in (("descricao", "descricao_revisao"), ("data", "data"), ("executado", "executado"),
                           ("verificado", "verificado"), ("aprovado", "aprovado")):
            cel = ultima.celulas.get(col)
            pares[chave] = (ultima.valor(col), cel.bbox if cel else ultima.bbox)
    folha = v.get("folha", "")
    m = re.search(r"/\s*(\d+)", folha)
    if m:
        pares["total_folhas"] = (str(int(m.group(1))), _alvo(car, "folha"))
    for chave in ctx.p("CAR-02")["campos_comparados"]:
        esperado = str(f.get(chave, "") or "").strip()
        if not esperado or chave not in pares or pares[chave][0] is None:
            continue
        valor, alvo = pares[chave]
        a, b = _comparavel(valor), _comparavel(esperado)
        if chave == "data":
            da, db = _data(valor), _data(esperado)
            igual = da is not None and db is not None and da == db
        elif chave == "total_folhas":
            igual = valor.lstrip("0") == esperado.lstrip("0")
        else:
            igual = a == b
        if not igual:
            ctx.add("CAR-02", pag.indice, alvo, campo=_nome_campo(chave), valor_pdf=valor, valor_ficha=esperado)
