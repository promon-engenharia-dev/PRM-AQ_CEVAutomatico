# Decisões já tomadas com o usuário

Não rediscuta estas decisões sem motivo novo. O histórico completo está no `CATALOGO_DE_REGRAS.md` §5, §7.4 e §7.5.

| # | Decisão |
|---|---|
| Cores | A ferramenta **só gera vermelho**. Amarelo, azul e verde são do verificador humano (PEG0005 6.4.2 e 7.3) |
| Q1 (revista) | Cada achado leva caixa de texto explicativo com seta, mais uma marcação translúcida vermelha: faixa sobre o texto, ou retângulo em volta da área. A seta separada aparece só nas ocorrências adicionais (corrige a seta duplicada). A nuvem continua disponível no `regras.json` |
| Q2 / Q2-b | Alturas nominais de 1,5 e 2,0 mm, no máximo 4,0 mm no carimbo. A regra vale só para notas, tags, keynotes, cotas e corpo de tabela. Títulos, bolhas e nomes de ambiente são classes do template |
| Q3 | FL = Folha. Sai do vocabulário de keynotes |
| Q4 | Família H (relatórios) adiada |
| Q5 | Comentário começa com `CV-AQ-nnn`. O código da regra fica só no CSV e no `/NM` |
| Q6 | Cota "quebrada" entra como ATENÇÃO, "a validar pelo verificador" |
| Q7 | A ficha é deduzida automaticamente: classe pelo número do documento, esquema de revisão pela revisão. A interface explica cada campo ao passar o mouse |
| Q8 | Lote 1 implementado como teste e comparado com os CEVs |
| Ocorrências | Toda ocorrência é marcada. Uma caixa por folha, com o máximo de 12 setas |
| TAG-01/02 agrupadas | Um comentário por folha, listando até 6 ambientes, com marca em cada TAG. Com um só ambiente, sai o texto individual (28/10/2026) |
| L1 | LD localizada por: campo na ficha, depois a última LD usada na operação, depois busca de `*-PL2-*.xlsx` até 4 pastas acima. Só serve LD da mesma operação |
| L2 | Abreviação no título conta como divergência (ATENÇÃO), mostrada palavra a palavra |
| L3 | A lista de referências pode citar o Nº Promon ou o Nº Cliente |
| Interface | Tudo em HTML (pywebview/WebView2), com Tkinter de reserva. Padrão visual Promon, logo ao lado do nome e modo escuro seguindo o Windows |
| Saídas | `_CEV.pdf` sempre. HTML (padrão ligado) e CSV (padrão desligado) são opcionais, e a escolha do operador fica lembrada |
| Quadros | Quadro de Ambientes e Quadro de Áreas só nas plantas gerais, não em ampliações (TAB-01, 28/10/2026) |
| Setorização | Planta-chave de layout/departamentos nas plantas gerais, seguindo o padrão `padroes/padrao-setorizacao.html` (`regras.json → setorizacao`). Proposta em 28/10/2026, aguardando aprovação do padrão. A falta da planta-chave (PRA-12) é cobrada em **todos os projetos** (30/10/2026) |
| Disciplina | A ferramenta é específica de Arquitetura (AQ). Outra disciplina pede catálogo próprio |
| Distribuição | Executável único (PyInstaller, onefile e windowed) em `dist\VerificadorCEV`, mais `verificador-cmd.exe` (console) para o cmd |
