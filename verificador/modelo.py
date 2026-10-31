"""Estruturas de dados compartilhadas.

Todas as coordenadas são em pontos PDF no espaço de EXIBIÇÃO da página
(já com /Rotate aplicado, origem no canto superior esquerdo, y para baixo).
A conversão para o espaço não girado só acontece no anotador.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import fitz


@dataclass
class Linha:
    texto: str
    bbox: fitz.Rect
    fonte: str
    tamanho: float          # corpo em pt
    cor: int                # sRGB inteiro (0xRRGGBB)
    flags: int
    horizontal: bool        # direção de leitura horizontal na exibição
    pagina: int             # índice 0-based
    chars: list = field(default_factory=list, repr=False, compare=False)  # [(x0, x1, c)] na exibição

    @property
    def cx(self) -> float:
        return (self.bbox.x0 + self.bbox.x1) / 2

    @property
    def cy(self) -> float:
        return (self.bbox.y0 + self.bbox.y1) / 2

    @property
    def italico(self) -> bool:
        return bool(self.flags & 2) or "italic" in self.fonte.lower() or "oblique" in self.fonte.lower()

    @property
    def negrito(self) -> bool:
        return bool(self.flags & 16) or "bold" in self.fonte.lower()


@dataclass
class Pagina:
    indice: int
    rect: fitz.Rect
    rotacao: int
    linhas: list[Linha] = field(default_factory=list)
    carimbo: "Carimbo | None" = None
    tabelas: list["Tabela"] = field(default_factory=list)
    vistas: list["Vista"] = field(default_factory=list)


@dataclass
class CampoCarimbo:
    valor: str
    linhas: list[Linha]

    @property
    def bbox(self) -> fitz.Rect:
        r = fitz.Rect(self.linhas[0].bbox)
        for l in self.linhas[1:]:
            r |= l.bbox
        return r


@dataclass
class LinhaHistorico:
    celulas: dict[str, CampoCarimbo]

    def valor(self, coluna: str) -> str:
        c = self.celulas.get(coluna)
        return c.valor if c else ""

    @property
    def bbox(self) -> fitz.Rect:
        r = None
        for c in self.celulas.values():
            r = c.bbox if r is None else r | c.bbox
        return r


@dataclass
class Carimbo:
    modelo: str
    area: fitz.Rect
    campos: dict[str, CampoCarimbo]
    rotulos: dict[str, Linha]
    historico: list[LinhaHistorico]   # da mais antiga para a mais recente


@dataclass
class LinhaTabela:
    celulas: dict[str, list[Linha]]   # nome da coluna -> linhas de texto
    bbox: fitz.Rect

    def texto(self, coluna: str) -> str:
        return " ".join(l.texto for l in self.celulas.get(coluna, [])).strip()


@dataclass
class Tabela:
    titulo: Linha
    cabecalho: list[Linha]
    linhas: list[LinhaTabela]
    area: fitz.Rect
    pagina: int

    @property
    def nome(self) -> str:
        return self.titulo.texto


@dataclass
class Vista:
    titulo: Linha
    escala: Linha | None
    area: fitz.Rect | None = None   # região da folha ocupada pela vista (acima do título)
    tipo: str = ""
    so_nivel: bool = False          # título só com o nome do nível (ex.: "TÉRREO"), sem o tipo da vista


@dataclass
class Achado:
    regra: str
    severidade: str
    pagina: int
    alvo: fitz.Rect            # região apontada (espaço de exibição)
    texto: str                 # comentário já formatado (sem a TAG CV-AQ)
    regiao: bool = False       # True: marcar com nuvem; False: só a seta
    dados: dict = field(default_factory=dict)
    indice: int = 0            # preenchido na numeração CV-AQ-nnn
    extras: list = field(default_factory=list)   # outras ocorrências na mesma folha (cada uma é marcada)


@dataclass
class Documento:
    caminho: str
    paginas: list[Pagina]
    nome_base: str

    def todas_linhas(self):
        for p in self.paginas:
            yield from p.linhas
