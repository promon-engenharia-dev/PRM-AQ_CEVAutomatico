---
name: cev-arquitetura
description: Método para manter e evoluir o Verificador de Projetos de Arquitetura (CEV automática): criar, ajustar, ativar ou rebaixar regras de verificação, validá-las contra os CEVs de referência, mexer nas anotações vermelhas do PDF, na ficha, na LD, na interface Promon e gerar o executável. Use sempre que a tarefa tocar em regras.json, verificador/regras/, CATALOGO_DE_REGRAS.md, anotador, interface ou distribuição desta ferramenta. Não serve para verificar PDFs com IA — a verificação é feita pela própria ferramenta, localmente.
---

# Verificador de Projetos — Arquitetura: manutenção

As regras inegociáveis estão no `CLAUDE.md` da raiz: 100% local, só vermelho, só apresentação, original intacto, documentos fora do Git e perguntar antes de assumir. Esta skill traz o **como fazer**.

**Duas versões.** Esta skill mantém a **versão offline** e o código comum. A **versão Claude** (skill `revisao-assistida-arquitetura`) usa o mesmo `regras.json` (seção `revisao_assistida`), o mesmo anotador e o mesmo relatório (`verificador/revisao.py`, opção `--revisao`).
- Toda mudança em regra, `regras.json`, anotação ou relatório vale para as duas versões.
- Feche a mudança com `python -X utf8 ferramentas/checar_alinhamento.py` sem erros.
- Lacunas da offline encontradas pela versão Claude entram aqui como proposta de regra ou correção.

## Mapa do código

| Onde | O que |
|---|---|
| `regras.json` | Todos os parâmetros e textos. `regras.<CÓDIGO>` tem `ativa`, `lote`, `severidade`, `comentario`, parâmetros próprios e `status_teste` |
| `verificador/extracao.py` | Texto com caixa de cada caractere (rawdict), em coordenadas de exibição. Filtra anotações SHX do AutoCAD e comentários de rodadas anteriores achatados no conteúdo |
| `verificador/carimbo.py` | Reconhece o modelo de carimbo por rótulos âncora (`carimbo.modelos`) |
| `verificador/tabelas.py`, `blocos.py` | Tabelas (título TABELA/QUADRO + coluna TAG), blocos-título, vistas e recorte das vistas |
| `verificador/ld.py` | Leitura da LD (xlsx via zipfile, sem openpyxl), localização e memória por operação |
| `verificador/regras/<família>.py` | Uma função `verificar(ctx)` por família: carimbo, prancha, tabelas, keynotes, conteudo, ld, apresentacao, vocabulario |
| `verificador/regras/__init__.py` | `Contexto` (`ctx.ativa`, `ctx.p`, `ctx.add`) e `executar` |
| `verificador/anotador.py` | Grava as anotações vermelhas com `saveIncr()` |
| `verificador/relatorio.py`, `nucleo.py`, `cli.py` | CSV/HTML, fluxo comum à CLI e à janela, linha de comando |
| `verificador/interface_web.py` + `web/index.html` | Janela HTML (pywebview/WebView2). `interface.py` + `tema.py` é a reserva em Tkinter |
| `ferramentas/validar_referencias.py` | Validação contra os CEVs de referência |
| `ferramentas/gerar_exe.bat` | Executável PyInstaller |
| `verificador/revisao.py`, `ferramentas/preparar_revisao.py` | Versão Claude: importação dos achados RA e preparo da revisão |
| `ferramentas/checar_alinhamento.py` | Confere o alinhamento entre as duas versões |

## Procedimento: regra nova ou ajuste de regra

1. **Evidência primeiro.** Antes de escrever código, mostre ao usuário de onde vem a regra:
   - comentários vermelhos recorrentes nos CEVs de referência (quantas ocorrências, em quantos arquivos);
   - item do CheckList de Arquitetura;
   - PEG0005 ou PEG0007.

   Se a regra pede saber o que um traço representa ou decidir se algo está tecnicamente certo, ela não entra (`references/fora-de-escopo.md`).
2. **Proponha e pergunte.** Escreva a proposta no catálogo, na família certa, com código, regra, severidade, parâmetro, texto do comentário, fonte e lote. As dúvidas vão como perguntas numeradas. Não implemente antes da aprovação.
3. **Parâmetros no `regras.json`.** Crie `regras.<CÓDIGO>` com `ativa: false`, `lote`, `severidade` (`ERRO` ou `ATENCAO`), `comentario` com `{campos}` e os parâmetros. O texto do comentário é imperativo e curto. Ele não leva o código da regra, que vai só no CSV e no `/NM`.
4. **Código.** Escreva na função `verificar(ctx)` da família:
   - teste `if ctx.ativa("XXX-nn")`;
   - leia os parâmetros com `ctx.p("XXX-nn")`;
   - registre o achado com `ctx.add("XXX-nn", pagina, rect, regiao=..., extras=[rects], **valores)`;
   - use `regiao=True` quando o alvo for uma área (tabela, campo do carimbo) e `extras` para as demais ocorrências na mesma folha.
5. **Valide** (`references/validacao.md`):
   - rode com `--lote N` para testar sem ativar;
   - compare com as marcas humanas;
   - teste também nos PDFs originais sem CEV.
6. **Decida o lote com os números** e mostre-os ao usuário:
   - poucos achados e reais → `ativa: true` e `status_teste` com data e resumo;
   - barulhenta → lote 2 ou 3, com o motivo no catálogo.
7. **Registre** no catálogo: a tabela da família, a decisão e o resultado do teste. Atualize `references/regras-ativas.md` desta skill.
8. **Alinhe.** Se a regra nova cobre um tema que estava em `references/fora-de-escopo.md`, atualize a linha correspondente e o critério RA da versão Claude. Depois, rode `ferramentas/checar_alinhamento.py`.

## Severidade e lotes

- **ERRO:** divergência objetiva, com certeza alta.
- **ATENÇÃO:** heurística; o verificador confirma. Na dúvida, use ATENÇÃO.
- **Lote 1:** determinística. **Lote 2:** depende de heurística de layout e precisa de calibração. **Lote 3:** candidata fraca ou sem evidência.

## Anotação: o que não pode mudar sem pedir

- **Cor:** tudo vermelho, `[1 0 0]`.
- **Caixa de texto:** caixa de texto explicativo (`/FreeText`, `/IT /FreeTextCallout`, Arial Narrow 10 pt), colocada em espaço livre da folha.
- **Marcação do trecho:**
  - faixa translúcida (opacidade 0,4) sobre um texto;
  - retângulo translúcido (opacidade 0,25) em volta de uma área.
- **Setas:** a 1ª ocorrência usa só a seta da própria caixa. Uma seta `/Line` separada aparece só nas ocorrências seguintes, no máximo 12.
- **Ocorrências:** uma caixa por folha (`agrupar_entre_folhas: false`), com sufixo "(N ocorrências nesta folha)".
- **TAG:** `CV-{especialidade}-{indice:03d}`, numerada da folha 1 até a última, de cima para baixo e da esquerda para a direita.
- **Saída:** `X.pdf` → `X_CEV.pdf`; se a entrada já é um CEV (`_CEV\d*`), → `X_CEV_auto.pdf`.

## Interface e relatório

Siga o padrão Promon (`../promon-parametros-formatacao.md`, fora do repositório; resumo em `references/padrao-visual.md`). A página não pode carregar nada da internet. O relatório HTML é um arquivo único, com o logo embutido em base64.

## Executável

Depois de mudar código ou `regras.json`:
1. Rode `ferramentas\gerar_exe.bat`.
2. Teste o exe sozinho numa pasta fora do projeto.
3. Compare os CSVs com os da versão Python.
4. Abra a janela pelo `Verificador.bat`.

Recursos novos (imagens, dados) precisam de `--add-data` no `.bat`, e o caminho em modo congelado vem de `sys._MEIPASS`.

## Referências desta skill

- `references/regras-ativas.md`: estado de cada regra e o porquê.
- `references/decisoes.md`: decisões já tomadas com o usuário. Não as rediscuta sem motivo novo.
- `references/fora-de-escopo.md`: o que não automatizar e por quê.
- `references/validacao.md`: como validar e como ler os números.
- `references/padrao-visual.md`: resumo do padrão Promon aplicado.
