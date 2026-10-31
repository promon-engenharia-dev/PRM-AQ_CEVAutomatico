"""Achados da revisão assistida (versão Claude) gravados num JSON.

A skill revisao-assistida-arquitetura escreve <arquivo>.revisao.json; aqui ele vira
uma lista de Achado, que entra no mesmo _CEV.pdf, CSV e relatório da versão offline.
Este módulo só lê um arquivo local: não faz chamada de rede.

Formato:
{
  "versao": 1,
  "achados": [
    {"regra": "RA-06", "severidade": "ERRO" | "ATENCAO" | "CORRETO", "folha": 1,
     "ancora": "texto que aparece na folha"            (ou)
     "retangulo_mm": [x0, y0, x1, y1],                 (folha como exibida, origem no canto superior esquerdo)
     "todas_ocorrencias": false,
     "titulo": "...", "comentario": "...", "acao": "...", "base": "Critério de Projeto 4.2"}
  ]
}
"""
from __future__ import annotations

import json

import fitz

from .config import Config, normalizar
from .modelo import Achado, Documento


def _localizar(item: dict, doc: Documento, cfg: Config, avisos: list) -> tuple[int, list[fitz.Rect]]:
    pagina = int(item.get("folha", 1)) - 1
    if not 0 <= pagina < len(doc.paginas):
        avisos.append(f"{item.get('regra')}: folha {pagina + 1} não existe; achado posto na folha 1.")
        pagina = 0
    pag = doc.paginas[pagina]
    if item.get("retangulo_mm"):
        x0, y0, x1, y1 = (cfg.mm_para_pt(v) for v in item["retangulo_mm"])
        return pagina, [fitz.Rect(x0, y0, x1, y1) & pag.rect]
    ancora = normalizar(item.get("ancora", ""))
    if ancora:
        achou = [l.bbox for l in pag.linhas if ancora in normalizar(l.texto)]
        if achou:
            return pagina, achou if item.get("todas_ocorrencias") else achou[:1]
        avisos.append(f"{item.get('regra')}: texto \"{item['ancora']}\" não encontrado na folha {pagina + 1}; "
                      f"achado posto no carimbo.")
    else:
        avisos.append(f"{item.get('regra')}: sem 'ancora' nem 'retangulo_mm'; achado posto no carimbo.")
    alvo = pag.carimbo.area if pag.carimbo else fitz.Rect(pag.rect.x1 - 200, pag.rect.y1 - 120, pag.rect.x1 - 20, pag.rect.y1 - 20)
    return pagina, [alvo]


def carregar(caminho: str, doc: Documento, cfg: Config, avisos: list | None = None) -> list[Achado]:
    avisos = avisos if avisos is not None else []
    ra = cfg["revisao_assistida"]
    with open(caminho, encoding="utf-8") as f:
        dados = json.load(f)
    achados = []
    for item in dados.get("achados", []):
        codigo = item.get("regra", "")
        if codigo not in ra["criterios"]:
            avisos.append(f"Critério {codigo!r} não existe em regras.json → revisao_assistida.criterios; achado ignorado.")
            continue
        sev = item.get("severidade", "ATENCAO").upper().replace("Ç", "C").replace("Ã", "A")
        if sev not in ra["severidades"]:
            avisos.append(f"{codigo}: severidade {item.get('severidade')!r} inválida; usada ATENCAO.")
            sev = "ATENCAO"
        pagina, alvos = _localizar(item, doc, cfg, avisos)
        texto = ra["formato_comentario"].format(
            comentario=item.get("comentario", "").strip(),
            acao=ra["prefixo_acao"] + item["acao"].strip() if item.get("acao") else "",
            base=ra["formato_base"].format(base=item["base"].strip()) if item.get("base") else "")
        achados.append(Achado(regra=codigo, severidade=sev, pagina=pagina, alvo=alvos[0], texto=texto,
                              regiao=bool(item.get("retangulo_mm")), extras=alvos[1:],
                              dados={"origem": "claude", "titulo": item.get("titulo", ""), "base": item.get("base", "")}))
    return achados
