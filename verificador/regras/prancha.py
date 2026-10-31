"""Família A — prancha/folha (PRA)."""
from __future__ import annotations

import re

import fitz

from ..extracao import dentro, mesma_linha


def _folha(pag):
    car = pag.carimbo
    if not car or "folha" not in car.campos:
        return None
    c = car.campos["folha"]
    m = re.match(r"^\s*(?:FL\.?\s*)?(\d{1,3})\s*/\s*(\d{1,3})\s*$", c.valor)
    if not m:
        return None
    alvo = c.bbox if c.linhas else car.rotulos["folha"].bbox
    return int(m.group(1)), int(m.group(2)), c.valor, alvo


def verificar(ctx):
    cfg = ctx.cfg
    doc = ctx.doc
    eh_prancha = ctx.classe in cfg["ficha"]["deducao_automatica"]["classes_prancha"]

    # PRA-01: blocos obrigatórios (escopo documento)
    edificacao = any(re.match(ctx.p("PRA-01")["regex_edificacao"], l.texto) for l in doc.todas_linhas())
    if eh_prancha and edificacao and ctx.ativa("PRA-01"):
        presentes = {b.nome for bl in ctx.blocos.values() for b in bl}
        p0 = doc.paginas[0]
        alvo = p0.carimbo.area if p0.carimbo else fitz.Rect(p0.rect.x1 - 300, 20, p0.rect.x1 - 20, 120)
        for nome in ctx.p("PRA-01")["blocos_obrigatorios"]:
            if nome not in presentes:
                ctx.add("PRA-01", 0, fitz.Rect(alvo.x0, alvo.y0, alvo.x1, alvo.y0 + 20), bloco=nome)

    # PRA-05 / PRA-06 / PRA-07: numeração de folhas
    folhas = [(pag, _folha(pag)) for pag in doc.paginas]
    validas = [(pag, f) for pag, f in folhas if f]
    total_ficha = str(ctx.ficha.get("total_folhas") or "").strip()
    if ctx.ativa("PRA-05") and total_ficha.isdigit():
        for pag, (x, y, txt, alvo) in validas:
            if y != int(total_ficha):
                ctx.add("PRA-05", pag.indice, alvo, x=f"{x:02d}", y=f"{y:02d}", total_ficha=total_ficha)
    if ctx.ativa("PRA-06") and validas:
        com = ctx.p("PRA-06")["comentarios"]
        n = len(doc.paginas)
        totais = sorted({f[1] for _, f in validas})
        if len(totais) > 1:
            pag, f = validas[0]
            ctx.add("PRA-06", pag.indice, f[3], detalhe=com["totais_diferentes"].format(totais=", ".join(map(str, totais))))
        for i, (pag, (x, y, txt, alvo)) in enumerate(validas):
            if x > y:
                ctx.add("PRA-06", pag.indice, alvo, detalhe=com["x_maior"].format(x=x, y=y))
            elif y < n and len(validas) == n:
                ctx.add("PRA-06", pag.indice, alvo, detalhe=com["total_menor"].format(x=x, y=y, n=n))
            if i > 0 and x != validas[i - 1][1][0] + 1:
                ctx.add("PRA-06", pag.indice, alvo, detalhe=com["sequencia"].format(esperado=validas[i - 1][1][0] + 1, x=x))
    if ctx.ativa("PRA-07"):
        p = ctx.p("PRA-07")["folha"]
        for pag, (x, y, txt, alvo) in validas:
            if not re.match(p["regex_formato_ok"], txt.strip()):
                ctx.add("PRA-07", pag.indice, alvo, formato=p["formato_padrao"].format(x=x, y=y))

    # PRA-08 / PRA-09: documentos de referência (cada folha tem a sua lista)
    p8 = ctx.p("PRA-08")["referencias"]
    rx_cit = re.compile(r"(?<![\d/])/\s*(\d{1,2})\s*/(?![\d/])")
    rx_nota = re.compile(p8["regex_nota"], re.I)
    rx_item = re.compile(r"^\s*(\d{1,2})\s*[.)\-]?\s*(.*)$")
    rx_cod = re.compile(ctx.p("PRA-09")["referencias"]["regex_codigo_documento"])
    for pag in doc.paginas:
        itens: set[int] = set()
        notas: set[int] = set()
        codigos: dict[str, list] = {}
        areas_txt = []
        for b in ctx.blocos[pag.indice]:
            if b.nome == "NOTAS GERAIS":
                notas |= {int(m.group(1)) for l in b.corpo if (m := rx_item.match(l.texto)) and not m.group(2)[:1].isdigit()}
                areas_txt.append(b.area)
            if b.nome != p8["bloco"]:
                continue
            areas_txt.append(b.area)
            numeros = []
            for l in b.corpo:
                m = rx_item.match(l.texto)
                if m and (m.group(2) == "" or rx_cod.search(l.texto)):
                    itens.add(int(m.group(1)))
                    numeros.append((l, m.group(1)))
            for l in b.corpo:
                for c in rx_cod.findall(l.texto):
                    m = rx_item.match(l.texto)
                    num = m.group(1) if m and m.group(2) else next(
                        (n for ln, n in numeros if ln is not l and mesma_linha(ln, l) and ln.bbox.x0 < l.bbox.x0), "?")
                    codigos.setdefault(c, []).append((l, num))
        if ctx.ativa("PRA-08") and itens:
            area_car = pag.carimbo.area if pag.carimbo else None
            faltas: dict[tuple, list] = {}
            for l in pag.linhas:
                if dentro(l, area_car) or any(dentro(l, a) for a in areas_txt):
                    continue
                for m in rx_cit.finditer(l.texto):
                    n = int(m.group(1))
                    eh_nota = bool(rx_nota.search(l.texto[: m.start()].rstrip()))
                    if (eh_nota and notas and n not in notas) or (not eh_nota and n not in itens):
                        faltas.setdefault((eh_nota, n), []).append(l)
            for (eh_nota, n), ls in faltas.items():
                extras = [x.bbox for x in ls[1:]]
                if eh_nota:
                    ctx.add("PRA-08", pag.indice, ls[0].bbox, chave="comentario_nota", extras=extras, n=n, max=max(notas))
                else:
                    ctx.add("PRA-08", pag.indice, ls[0].bbox, extras=extras, n=n)
        if ctx.ativa("PRA-09"):
            for cod, ocs in codigos.items():
                nums = sorted({o[1] for o in ocs})
                if len(ocs) > 1 and len(nums) > 1:
                    ctx.add("PRA-09", pag.indice, ocs[1][0].bbox, i=nums[0], j=nums[1], codigo=cod)

    # PRA-10: textos provisórios
    if ctx.ativa("PRA-10"):
        rxs = [re.compile(r) for r in ctx.p("PRA-10")["placeholders"]["regex"]]
        for pag in doc.paginas:
            grupos: dict[str, list] = {}
            for l in pag.linhas:
                if any(r.search(l.texto) for r in rxs):
                    grupos.setdefault(l.texto, []).append(l)
            for txt, ls in grupos.items():
                ctx.add("PRA-10", pag.indice, ls[0].bbox, extras=[x.bbox for x in ls[1:]], texto=txt[:60])

    # PRA-11: remissão a folha inexistente
    if ctx.ativa("PRA-11"):
        total = int(total_ficha) if total_ficha.isdigit() else max((f[1] for _, f in validas), default=0)
        rx = re.compile(ctx.p("PRA-11")["remissao_folha"]["regex"])
        if total:
            for pag in doc.paginas:
                area_car = pag.carimbo.area if pag.carimbo else None
                for l in pag.linhas:
                    if dentro(l, area_car):
                        continue
                    for m in rx.finditer(l.texto):
                        if int(m.group("n")) > total:
                            ctx.add("PRA-11", pag.indice, l.bbox, codigo=m.group(0), total=total)
