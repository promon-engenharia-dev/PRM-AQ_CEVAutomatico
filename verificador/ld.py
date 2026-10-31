"""Lista de Documentos (LD) do projeto: leitura do .xlsx padrão Promon e localização do arquivo.

Lê o xlsx só com a biblioteca padrão (zip + XML), sem dependência nova e sem rede.
"""
from __future__ import annotations

import glob
import html
import json
import os
import re
import zipfile
from dataclasses import dataclass

from .config import Config, normalizar


@dataclass
class DocLD:
    promon: str
    cliente: str
    titulo: str
    acao: str          # D documento · A atividade · M modelagem · E excluir


def chave(codigo: str) -> str:
    return re.sub(r"\s+", "", codigo or "").upper()


class ListaDocumentos:
    def __init__(self, caminho: str, docs: list[DocLD]):
        self.caminho = caminho
        self.docs = docs
        self.indice: dict[str, DocLD] = {}
        for d in docs:
            for c in (d.promon, d.cliente):
                if c:
                    self.indice.setdefault(chave(c), d)

    def busca(self, codigo: str) -> DocLD | None:
        return self.indice.get(chave(codigo))


# leitura do xlsx --------------------------------------------------------------

def _texto(xml: str) -> str:
    return html.unescape("".join(re.findall(r"<t[^>]*>(.*?)</t>", xml, re.S)))


def _abas(z: zipfile.ZipFile) -> dict[str, str]:
    wb = z.read("xl/workbook.xml").decode("utf8")
    rels = z.read("xl/_rels/workbook.xml.rels").decode("utf8")
    alvo = {}
    for m in re.finditer(r"<Relationship\b([^>]*)/?>", rels):
        a = m.group(1)
        i, t = re.search(r'Id="([^"]+)"', a), re.search(r'Target="([^"]+)"', a)
        if i and t:
            alvo[i.group(1)] = t.group(1)
    out = {}
    for m in re.finditer(r"<sheet\b([^>]*)/?>", wb):
        a = m.group(1)
        nome, rid = re.search(r'name="([^"]+)"', a), re.search(r'r:id="([^"]+)"', a)
        if nome and rid and rid.group(1) in alvo:
            t = alvo[rid.group(1)].lstrip("/")
            out[html.unescape(nome.group(1))] = t if t.startswith("xl/") else "xl/" + t
    return out


def _linhas(z: zipfile.ZipFile, caminho: str, ss: list[str]):
    x = z.read(caminho).decode("utf8")
    for row in re.finditer(r"<row\b[^>]*>(.*?)</row>", x, re.S):
        d = {}
        for m in re.finditer(r'<c r="([A-Z]+)\d+"([^>]*?)(?:/>|>(.*?)</c>)', row.group(1), re.S):
            col, attrs, corpo = m.groups()
            if not corpo:
                continue
            v = re.search(r"<v>(.*?)</v>", corpo, re.S)
            if v:
                d[col] = ss[int(v.group(1))] if 't="s"' in attrs else v.group(1)
            else:
                d[col] = _texto(corpo)
        yield d


def ler(caminho: str, cfg: Config) -> ListaDocumentos:
    lc = cfg["ld"]
    nomes_hdr = {k: {normalizar(x).replace(" ", "") for x in v} for k, v in lc["cabecalho"].items()}
    with zipfile.ZipFile(caminho) as z:
        ss = []
        if "xl/sharedStrings.xml" in z.namelist():
            x = z.read("xl/sharedStrings.xml").decode("utf8")
            ss = [_texto(si) for si in re.findall(r"<si>(.*?)</si>", x, re.S)]
        abas = _abas(z)
        ordem = [a for a in lc["abas_preferidas"] if a in abas] + [a for a in abas if a not in lc["abas_preferidas"]]
        for aba in ordem:
            cols = None
            docs = []
            for i, d in enumerate(_linhas(z, abas[aba], ss)):
                if cols is None:
                    if i > lc["linhas_max_ate_cabecalho"]:
                        break
                    inv = {normalizar(v).replace(" ", ""): k for k, v in d.items()}
                    achadas = {campo: next((c for n, c in inv.items() if any(n.startswith(h) for h in hs)), None)
                               for campo, hs in nomes_hdr.items()}
                    if achadas["promon"] and achadas["titulo"]:
                        cols = achadas
                    continue
                p = d.get(cols["promon"], "").strip()
                if not p:
                    continue
                docs.append(DocLD(promon=p, cliente=d.get(cols["cliente"], "").strip() if cols["cliente"] else "",
                                  titulo=d.get(cols["titulo"], "").strip(),
                                  acao=d.get(cols["acao"], "").strip().upper() if cols["acao"] else ""))
            if docs:
                return ListaDocumentos(caminho, docs)
    raise ValueError(f"LD sem aba com colunas de número e título reconhecíveis: {os.path.basename(caminho)}")


# localização --------------------------------------------------------------------

def _memoria(nome: str = "lds.json") -> str:
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    return os.path.join(base, "VerificadorCEV", nome)


def ler_preferencias() -> dict:
    try:
        return json.load(open(_memoria("preferencias.json"), encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def gravar_preferencias(prefs: dict) -> None:
    arq = _memoria("preferencias.json")
    os.makedirs(os.path.dirname(arq), exist_ok=True)
    with open(arq, "w", encoding="utf-8") as f:
        json.dump(prefs, f, ensure_ascii=False, indent=2)


def lembrar(operacao: str, caminho: str) -> None:
    if not operacao:
        return
    arq = _memoria()
    os.makedirs(os.path.dirname(arq), exist_ok=True)
    try:
        dados = json.load(open(arq, encoding="utf-8"))
    except (OSError, ValueError):
        dados = {}
    dados[operacao] = os.path.abspath(caminho)
    with open(arq, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def lembrada(operacao: str) -> str | None:
    try:
        c = json.load(open(_memoria(), encoding="utf-8")).get(operacao)
        return c if c and os.path.isfile(c) else None
    except (OSError, ValueError):
        return None


def operacao_de(*codigos: str) -> str:
    """E.POTA001 a partir de E.POTA001-AQ3-00016 (ou vazio)."""
    for c in codigos:
        m = re.match(r"^(E\.[A-Z]{4}\d{3})", (c or "").strip().upper())
        if m:
            return m.group(1)
    return ""


def localizar(pdf: str, cfg: Config, ficha: dict | None, operacao: str = "") -> str | None:
    """Ordem: ficha → memória da operação → busca na pasta do PDF e nas pastas acima."""
    lc = cfg["ld"]
    c = (ficha or {}).get("ld")
    if c and os.path.isfile(c):
        return c
    c = lembrada(operacao)
    if c:
        return c
    pasta = os.path.dirname(os.path.abspath(pdf))
    for _ in range(lc["niveis_acima_na_busca"] + 1):
        cands = []
        for g in lc["padroes_nome"]:
            cands += [x for x in glob.glob(os.path.join(pasta, g)) if not os.path.basename(x).startswith("~$")]
        cands = sorted(set(cands), key=lambda x: (operacao not in os.path.basename(x).upper(), -os.path.getmtime(x)))
        if operacao:
            # com a operação conhecida, só serve a LD dela (outra LD geraria falsos "não consta")
            cands = [x for x in cands if operacao in os.path.basename(x).upper()]
        if cands:
            return cands[0]
        acima = os.path.dirname(pasta)
        if acima == pasta:
            break
        pasta = acima
    return None
