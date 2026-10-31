# Verificador de Projetos — Arquitetura (CEV automática)

Ferramenta Python + PyMuPDF que verifica pranchas de Arquitetura (especialidade AQ) em PDF e grava `<arquivo>_CEV.pdf` com comentários vermelhos `CV-AQ-nnn`.

## Duas versões, sempre alinhadas

| | Versão offline | Versão Claude |
|---|---|---|
| Como roda | `python -m verificador` / `verificador.exe` | skill **`revisao-assistida-arquitetura`** |
| O que verifica | Regras determinísticas de apresentação (`regras.json → regras`) | **Tudo da offline** + critérios RA (`regras.json → revisao_assistida`): fora de escopo da offline, critério de projeto, normas, questões técnicas |
| IA / rede | Nenhuma: 100% local | Claude (licença enterprise, autorizada pela usuária em 28/10/2026) |
| Saída | `_CEV.pdf`, HTML, CSV | os mesmos arquivos, gravados pelo mesmo código (`--revisao`) |

**Para manter as versões alinhadas:**
- Uma única fonte de parâmetros (`regras.json`) e um único código de anotação e relatório.
- A versão Claude sempre roda as regras offline antes.
- Achado mecânico do Claude vira proposta de regra offline.
- Toda mudança termina com `python -X utf8 ferramentas/checar_alinhamento.py` sem erros.

Para manter ou evoluir a ferramenta (regras, validação, anotação, interface, executável), use a skill **`cev-arquitetura`**.

## Regras que nunca podem ser quebradas

1. **Versão offline 100% local.** O `verificador` e o exe não usam IA, não fazem chamada de rede e não carregam nada da internet. A IA entra só pela skill da versão Claude.
2. **Só vermelho no PDF.** As anotações são sempre vermelhas (PEG0005 6.4.2), nas duas versões. O "Correto" da versão Claude aparece só no relatório.
3. **Escopo.** A versão offline cobre só a apresentação. A versão Claude pode apontar questões técnicas, sempre fundamentadas e com a base citada. A decisão final é do verificador.
4. **O original fica intacto.** Copiar o PDF e gravar com `saveIncr()`.
5. **Documentos fora do Git.** `referencias/`, `*.pdf`, fichas, `*.revisao.json`, `*_revisao/`, CSVs de saída e `saida_teste/` não são versionados. Não copiar trechos dos documentos para código, catálogo ou skills.
6. **Pergunte antes de assumir.** São preferíveis poucas regras confiáveis a muitas barulhentas. Toda regra offline nova é validada contra os CEVs de referência.
7. **Valores no `regras.json`.** Nada de números mágicos ou textos fixos no código.

## Comandos

```bash
python -X utf8 -m verificador arquivo.pdf                          # versão offline (CLI)
python -X utf8 -m verificador --janela                             # janela HTML
python -X utf8 ferramentas/preparar_revisao.py arquivo.pdf         # versão Claude: preparo
python -X utf8 -m verificador --revisao x.revisao.json arquivo.pdf # versão Claude: gravação
python -X utf8 ferramentas/validar_referencias.py                  # validação contra os CEVs
python -X utf8 ferramentas/checar_alinhamento.py                   # alinhamento entre as versões
ferramentas\gerar_exe.bat                                          # executável em dist\VerificadorCEV
```

## Documentos

- `CATALOGO_DE_REGRAS.md`: registro completo, com regras, decisões e histórico.
- `README.md`: uso e distribuição.
- Padrão visual Promon: `../promon-parametros-formatacao.md`.
