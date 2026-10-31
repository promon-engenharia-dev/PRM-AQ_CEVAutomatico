"""Confere se a versão offline e a versão Claude continuam alinhadas.

Uso:  python -X utf8 ferramentas/checar_alinhamento.py
Sai com código 1 se houver divergência. Rode depois de qualquer mudança em regras.json,
no catálogo, nas regras ou nas skills.
"""
from __future__ import annotations

import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(RAIZ, ".claude", "skills")


def ler(*partes: str) -> str:
    with open(os.path.join(RAIZ, *partes), encoding="utf-8") as f:
        return f.read()


def main() -> int:
    erros: list[str] = []
    cfg = json.loads(ler("regras.json"))
    catalogo = ler("CATALOGO_DE_REGRAS.md")

    # 1. toda regra offline está documentada no catálogo
    for codigo in cfg["regras"]:
        if not codigo.endswith("-comum") and codigo not in catalogo:
            erros.append(f"regras.json: {codigo} não aparece no CATALOGO_DE_REGRAS.md")

    # 2. critérios da versão Claude: regras.json × skill × catálogo
    ra = set(cfg["revisao_assistida"]["criterios"])
    criterios_md = ler(".claude", "skills", "revisao-assistida-arquitetura", "references", "criterios.md")
    no_md = set(re.findall(r"\bRA-\d{2}\b", criterios_md))
    for c in sorted(ra - no_md):
        erros.append(f"{c} está no regras.json, mas não em revisao-assistida-arquitetura/references/criterios.md")
    for c in sorted(no_md - ra):
        erros.append(f"{c} está na skill, mas não em regras.json → revisao_assistida.criterios")
    for c in sorted(ra):
        if c not in catalogo:
            erros.append(f"{c} não aparece no CATALOGO_DE_REGRAS.md")

    # 3. severidades aceitas pela importação
    if set(cfg["revisao_assistida"]["severidades"]) != {"ERRO", "ATENCAO", "CORRETO"}:
        erros.append("revisao_assistida.severidades deve ser exatamente ERRO, ATENCAO e CORRETO")

    # 4. arquivos citados pelas skills existem
    for skill in os.listdir(SKILLS):
        texto = ler(".claude", "skills", skill, "SKILL.md")
        for ref in set(re.findall(r"references/[\w\-]+\.md", texto)):
            alvo = os.path.join(SKILLS, skill, ref)
            if not os.path.isfile(alvo) and not re.search(r"cev-arquitetura/" + re.escape(ref), texto):
                erros.append(f"{skill}/SKILL.md cita {ref}, que não existe")
        for script in set(re.findall(r"ferramentas/[\w\-]+\.(?:py|bat)", texto)):
            if not os.path.isfile(os.path.join(RAIZ, script)):
                erros.append(f"{skill}/SKILL.md cita {script}, que não existe")

    # 5. fora de escopo da versão offline está coberto pela versão Claude
    fora = ler(".claude", "skills", "cev-arquitetura", "references", "fora-de-escopo.md")
    for c in sorted(set(re.findall(r"\bRA-\d{2}\b", fora)) - ra):
        erros.append(f"fora-de-escopo.md cita {c}, que não existe no regras.json")
    linhas_tabela = [l for l in fora.splitlines() if l.startswith("| ") and not l.startswith("| Tema") and "---" not in l]
    for l in linhas_tabela:
        if not re.search(r"\bRA-\d{2}\b", l):
            erros.append(f"fora-de-escopo.md: tema sem critério RA correspondente: {l[:60]}")

    if erros:
        print("DESALINHADO:")
        for e in erros:
            print(" -", e)
        return 1
    print(f"Alinhado: {len(cfg['regras'])} regras offline, {len(ra)} critérios da versão Claude, "
          f"{len(os.listdir(SKILLS))} skills.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
