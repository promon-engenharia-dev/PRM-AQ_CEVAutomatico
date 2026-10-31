# Verificador de Projetos — Arquitetura (CEV automática)

Ferramenta específica da disciplina de **Arquitetura**: as regras, o vocabulário e a TAG `CV-AQ-nnn` são da especialidade AQ.

Verificação mecânica de **apresentação** de pranchas e relatórios em PDF. Grava `<arquivo>_CEV.pdf` com comentários vermelhos (`CV-AQ-nnn`) e um CSV com a lista de achados.

- 100% local: nenhuma chamada de rede, nenhum arquivo sai da máquina.
- Gravação incremental: o PDF original, as anotações que já existem e as assinaturas digitais ficam intactos.
- Só gera vermelho (PEG0005 6.4.2). Juízo técnico de engenharia fica com o verificador.

Regras: [CATALOGO_DE_REGRAS.md](CATALOGO_DE_REGRAS.md). Parâmetros e textos dos comentários: [regras.json](regras.json). O código não tem valores fixos.

## Uso

**Janela:** dê dois cliques em `Verificador.bat`, ou arraste PDFs sobre ele, que eles já entram na lista.
Com a janela aberta, também dá para arrastar PDFs direto para a área "1 · Arquivos".
1. **Arquivos:** adicione os PDFs.
2. **Opções:** escolha a LD do projeto (vazio = busca automática da LD da operação), a pasta de saída e se quer
   a ficha da emissão (passe o mouse sobre o nome de cada campo para ver a explicação).
3. **Resultado:** o painel mostra os achados por severidade. Dois cliques num achado abrem o PDF anotado. Há
   botões para abrir o relatório HTML e a pasta.

A janela e o relatório seguem a identidade Promon (`promon-parametros-formatacao.md`), com o logo oficial ao lado do nome, e mudam para o modo
escuro quando o Windows está em modo escuro. A janela acompanha a troca de tema enquanto está aberta.

Para cada PDF é sempre gravado o `…_CEV.pdf` (anotações vermelhas). São opcionais, e escolhidos em
"Arquivos gravados" na janela: o **relatório HTML** (`…_CEV.html`, ligado por padrão) e a **lista em CSV** (`…_CEV.csv`,
desligada por padrão). A janela lembra a última escolha do operador. A avaliação "procede / não procede" é feita na
própria janela, e "Salvar avaliação" grava um CSV à parte para o piloto.

**Linha de comando:**

```bash
python -X utf8 -m verificador arquivo.pdf
```

| Opção | Efeito |
|---|---|
| `--janela` | abre a janela com os PDFs indicados |
| `--sem-ficha` | não compara com ficha |
| `--sem-formulario` | usa a `.ficha.json` existente, sem abrir o formulário |
| `--ficha caminho.json` | usa esta ficha |
| `--ld caminho.xlsx` / `--sem-ld` | usa esta LD / não usa LD |
| `--saida pasta` | grava a saída em outra pasta |
| `--csv` / `--sem-csv` | grava / não grava a lista em CSV (padrão: não grava) |
| `--html` / `--sem-html` | grava / não grava o relatório HTML (padrão: grava) |
| `--lote N` | TESTE: liga todas as regras até o lote N, ignorando `ativa` |
| `--ajuda-ficha` | explica cada campo da ficha |

Se o arquivo de entrada já for um CEV (`_CEV`, `_CEV1`, `_CEV2`), a saída vira `…_CEV_auto.pdf`.

## Validação contra os CEVs de referência

```bash
python -X utf8 ferramentas/validar_referencias.py
```

O script grava `saida_teste/validacao.csv`, com cada achado e o comentário seu mais próximo, e `saida_teste/validacao_resumo.txt`.

## Versão Claude (revisão assistida)

Há duas versões, sempre alinhadas:
- a **offline** (este programa e o exe), 100% local e sem IA;
- a **versão Claude**, a skill `revisao-assistida-arquitetura`, usada no Claude Code.

**O que a versão Claude faz:**
- roda todas as regras offline;
- acrescenta o que a offline deixa fora de escopo: TAGs e cotas faltando, conflito gráfico, coerência entre vistas, notas × desenho;
- compara o desenho com o **critério de projeto** da operação;
- aponta questões técnicas (normas, solução de projeto), sempre com a base citada.

O resultado sai no mesmo `_CEV.pdf`, só em vermelho, e no mesmo relatório, que ganha a severidade "Correto" e a origem de cada achado.

```bash
python -X utf8 ferramentas/preparar_revisao.py arquivo.pdf --criterio criterio.pdf
python -X utf8 -m verificador --sem-formulario --revisao arquivo_revisao/arquivo.revisao.json arquivo.pdf
python -X utf8 ferramentas/checar_alinhamento.py
```

No Claude Code, basta pedir "faça a revisão assistida deste PDF" e a skill conduz os passos. Os critérios ficam em `regras.json → revisao_assistida`, e o formato do JSON está na própria skill.

## Distribuição (executável)

Para quem vai só usar a ferramenta, não é preciso instalar Python. Basta entregar a pasta `dist\VerificadorCEV\`, que contém:

- `verificador.exe`: programa único (~40 MB) que já traz dentro o Python, as bibliotecas, a interface, os logos e o `regras.json`;
- `verificador-cmd.exe`: o mesmo programa com console, para rodar pelo cmd (`verificador-cmd arquivo.pdf`, opções em `--help`, código de saída 1 se algum PDF falhar);
- `Verificador.bat`: atalho para abrir a janela ou arrastar PDFs. Ele usa o exe automaticamente;
- `regras.json`: cópia editável dos parâmetros, lida no lugar da cópia interna. Se for apagada, o exe usa a interna;
- `LEIA-ME.txt`: instruções curtas para o usuário.

**Gerar de novo após mudanças no código:**

```bat
ferramentas\gerar_exe.bat
```

Os exes são gerados com o PyInstaller (`pip install pyinstaller`) em `--onefile`: o `verificador.exe` com `--windowed` e o `verificador-cmd.exe` com `--console`. Os arquivos de trabalho ficam em `%TEMP%\VerificadorCEV_build`. A pasta `dist/` não é versionada.

**Observações:**
- O `verificador.exe` abre sem console, por isso não mostra mensagens no cmd. Para a linha de comando, use o `verificador-cmd.exe`.
- O exe não é assinado digitalmente. O Windows SmartScreen pode avisar na primeira execução (clique em "Mais informações" → "Executar assim mesmo"), principalmente se o arquivo vier por e-mail ou Teams. Distribuir pela pasta do SharePoint/OneDrive costuma evitar o aviso.
- A primeira abertura leva alguns segundos, porque o exe se descompacta numa pasta temporária.
## Requisitos

Python 3.10+ e as bibliotecas de `requirements.txt` (`pip install -r requirements.txt`): PyMuPDF e pywebview.
A janela usa o WebView2 (motor do Edge, já presente no Windows 11). Se ele faltar, a ferramenta abre uma
janela simples em Tkinter no lugar.

`referencias/`, PDFs, fichas e `saida_teste/` não são versionados (`.gitignore`).
