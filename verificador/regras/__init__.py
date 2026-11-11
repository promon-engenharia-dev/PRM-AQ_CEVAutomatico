"""Execução das regras. Cada família expõe `verificar(ctx)`."""
from __future__ import annotations

import re

import fitz

from ..blocos import detectar_blocos
from ..carimbo import reconhecer
from ..config import Config
from ..modelo import Achado, Documento
from ..tabelas import detectar_tabelas, detectar_vistas, recortar_vistas


class Contexto:
    def __init__(self, doc: Documento, cfg: Config, ficha: dict | None, ld=None):
        self.ld = ld
        self.doc = doc
        self.cfg = cfg
        self.ficha = ficha or {}
        self.achados: list[Achado] = []
        self.blocos = {}
        for p in doc.paginas:
            p.carimbo = reconhecer(p, cfg)
            self.blocos[p.indice] = detectar_blocos(p, cfg)
            p.tabelas = detectar_tabelas(p, cfg, [b.area for b in self.blocos[p.indice]])
            p.vistas = detectar_vistas(p, cfg)
            recortar_vistas(p, cfg, self.areas_texto(p))
        self.classe = classe_documento(doc.nome_base, cfg, self.ficha)

    def areas_texto(self, p) -> list:
        """Tabelas, blocos de texto e carimbo: o que não faz parte de nenhuma vista."""
        return [t.area for t in p.tabelas] + [b.area for b in self.blocos[p.indice]] + ([p.carimbo.area] if p.carimbo else [])

    def desenhos(self, indice: int) -> tuple[list, fitz.Matrix]:
        """Vetores da folha (get_drawings) e a matriz para o espaço de exibição.
        Lidos uma vez só: são a parte mais lenta da verificação."""
        cache = self.__dict__.setdefault("_desenhos", {})
        if indice not in cache:
            with fitz.open(self.doc.caminho) as pdf:
                page = pdf[indice]
                cache[indice] = (page.get_drawings(), page.rotation_matrix)
        return cache[indice]

    def ativa(self, codigo: str) -> bool:
        return self.cfg.ativa(codigo)

    def p(self, codigo: str) -> dict:
        return self.cfg.regra(codigo)

    def add(self, _regra: str, pagina: int, alvo: fitz.Rect, regiao: bool = False,
            chave: str = "comentario", severidade: str | None = None, extras=None, **valores):
        texto = self.cfg.comentario(_regra, chave, **valores)
        extras = [fitz.Rect(r) for r in (extras or [])]
        if extras:
            texto += self.cfg["anotacao"]["sufixo_ocorrencias"].format(n=len(extras) + 1)
        sev = severidade or self.cfg.regra(_regra)["severidade"]
        self.achados.append(Achado(regra=_regra, severidade=sev, pagina=pagina, alvo=fitz.Rect(alvo),
                                   texto=texto, regiao=regiao, dados=valores, extras=extras))


def classe_documento(nome_base: str, cfg: Config, ficha: dict) -> str | None:
    if ficha.get("classe_documento"):
        return ficha["classe_documento"]
    numero = re.sub(r"(_R[0-9A-Z]{1,2}|-P_[A-Z0-9]{1,2}|_[A-Z0-9]{1,2})?(_CEV\d*)?(_auto)?$", "", nome_base)
    numero = re.sub(r"-P$", "", numero)
    da = cfg["ficha"]["deducao_automatica"]
    for rx in da["classe_documento_regex"]:
        m = re.search(rx, numero)
        if m:
            return m.group("classe")
    m = re.search(da["classe_por_assunto"]["regex"], numero)       # numeração Promon E.*: assunto do PEG0007
    if m:
        return da["classe_por_assunto"]["mapa"].get(m.group("assunto"))
    return None


def executar(doc: Documento, cfg: Config, ficha: dict | None = None, ld=None) -> list[Achado]:
    from . import apresentacao, carimbo, composicao, conteudo, keynotes, prancha, setorizacao, tabelas, vocabulario
    from . import ld as fam_ld

    ctx = Contexto(doc, cfg, ficha, ld)
    for familia in (carimbo, prancha, setorizacao, composicao, tabelas, keynotes, conteudo, fam_ld, apresentacao, vocabulario):
        familia.verificar(ctx)
    return agrupar_folhas(ctx.achados, cfg["anotacao"]["agrupar_entre_folhas"])


def agrupar_folhas(achados: list[Achado], entre_folhas: bool = True) -> list[Achado]:
    """O mesmo comentário repetido em várias folhas (carimbo/tabela iguais em cada folha) sai uma vez só."""
    primeiro: dict[tuple, Achado] = {}
    outras: dict[tuple, list[int]] = {}
    saida = []
    posicoes = set()
    for a in achados:
        pos = (a.regra, a.texto, a.pagina, round(a.alvo.x0), round(a.alvo.y0))
        if pos in posicoes:
            continue                      # mesmo achado no mesmo lugar (texto duplicado sobreposto)
        posicoes.add(pos)
        chave = (a.regra, a.texto) if entre_folhas else (a.regra, a.texto, a.pagina, a.alvo.x0, a.alvo.y0)
        if chave in primeiro:
            if a.pagina != primeiro[chave].pagina:
                outras[chave].append(a.pagina)
                continue
        else:
            primeiro[chave], outras[chave] = a, []
        saida.append(a)
    for chave, pags in outras.items():
        if pags:
            folhas = ", ".join(str(p + 1) for p in sorted(set(pags)))
            primeiro[chave].texto += f" (também nas folhas {folhas})"
    return saida
