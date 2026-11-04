# Prompt — conversa de ideação sobre o Verificador CEV de Arquitetura

> Cole o texto abaixo numa conversa nova. Se puder, anexe `CATALOGO_DE_REGRAS.md`, `README.md` e `CLAUDE.md` deste repositório.

---

Quero usar esta conversa para **esclarecer, idealizar e fazer brainstorm** sobre uma ferramenta que estou desenvolvendo. **Não escreva nem altere código aqui.** O desenvolvimento acontece numa outra sessão do Claude Code; esta é para pensar. Quando uma ideia amadurecer, me ajude a transformá-la num pedido claro, que eu levo para a sessão de desenvolvimento.

## Quem sou e o contexto

- Sou verificadora de projetos de **Arquitetura** na Promon Engenharia.
- A verificação gera o **CEV**, uma cópia de verificação do PDF com comentários.
- Pelo PEG0005, a cor das marcas tem significado:
  - **vermelho** = corrigir;
  - **amarelo** = conforme;
  - **azul** e **verde** = outros atos do verificador.
- Projetos atuais: operação E.POTA001, com numeração de cliente 6110/7610 e numeração Promon E.*. Também há projetos antigos de outros clientes (T015/T012).

## O que a ferramenta é hoje — "Verificador de Projetos — Arquitetura"

**Base:** Python + PyMuPDF. Lê as pranchas em PDF e grava `<arquivo>_CEV.pdf`.
- **Anotações:** só vermelhas, sempre como `CV-AQ-nnn` + caixa de texto + seta + faixa ou retângulo translúcido.
- **Original preservado:** a gravação é incremental, então o original fica intacto.
- **Saídas opcionais:** relatório HTML (com "procede / não procede" para avaliar o piloto) e CSV.

**Duas versões, sempre alinhadas:**
- **Offline** (`verificador.exe`, janela HTML + `verificador-cmd.exe`):
  - 100% local, sem IA e sem rede;
  - só regras determinísticas de apresentação;
  - tudo parametrizado num `regras.json`.
- **Versão Claude** (skill `revisao-assistida-arquitetura`):
  - roda primeiro as regras offline;
  - acrescenta a análise do Claude: TAGs e cotas faltando, conflitos gráficos, coerência entre vistas, notas × desenho, **critério de projeto da operação** (assunto AQ1), normas (NBR 9050, NR-24, incêndio) e questões técnicas;
  - classifica os achados em Corrigir / Atenção / Correto;
  - grava no mesmo PDF e relatório, com a origem de cada achado indicada;
  - o uso de documentos com o Claude está coberto pela licença enterprise.
- **Garantia de alinhamento:** um script (`checar_alinhamento.py`) confere regras × catálogo × skills.

**Famílias de regras offline:**

| Família | O que confere |
|---|---|
| PRA | Folha e prancha |
| CAR | Carimbo e histórico |
| TAB | Tabelas |
| KEY | Keynotes tabela × desenho |
| TAG | TAG de ambiente, PD e acabamentos |
| APR | Apresentação |
| VOC | Vocabulário |
| CON | Informação faltante |
| LD | Conferência com a Lista de Documentos |

São mais de 80 regras catalogadas; cerca de metade está ativa. Toda regra nova é validada contra **40 CEVs de referência** e só é ativada se não gerar ruído. **Princípio:** poucas regras confiáveis são melhores que muitas barulhentas.

**Coisas recentes:**
- **Setorização:**
  - padrão proposto para a planta-chave de layout/departamentos: 13 setores com cor fixa, modelo de legenda e esquema de cores no template Revit;
  - regras de setorização ativas: falta de planta-chave, cores parecidas e legenda × planta.
- **Regras tiradas da comparação entre o CEV da automação e um CEV feito por mim:**
  - título de vista incompleto;
  - tabela encoberta;
  - código de emissão inválido;
  - telhas sem dimensão.
- **Interface e distribuição:** interface no padrão visual Promon, com modo escuro, e executável para distribuir sem instalar nada.

## Restrições que não mudam

- A versão offline continua sem IA e sem rede.
- O PDF só recebe marcas vermelhas.
- O original nunca é alterado.
- Documentos confidenciais nunca vão para o Git.
- Regra nova só entra com evidência (CEVs reais) e validação.

## Pendências e ideias já na mesa

- **Aprovação do padrão de setorização.** Depois dela, as regras de cor e nome de setor (PRA-13/15) podem ser ativadas.
- **Pré-visualização interativa no relatório:** folha renderizada com balões numerados por achado, clique no achado leva à posição na folha. Seria parecida com uma ferramenta de verificação de Instrumentação que colegas fizeram.
- **Vocabulário entre documentos da mesma operação:** por exemplo, TERRENO × TERRAPLENAGEM em PDFs diferentes.
- **Família de relatórios de texto** (memoriais, especificações): adiada por falta de referências.
- **Piloto com outros verificadores:** como medir "procede / não procede", e como decidir o que ativar ou rebaixar.
- **Regras ainda no lote 2 por falta de evidência:**
  - vistas desalinhadas;
  - descida de água pluvial;
  - cotas entre eixos;
  - altura de texto e sobreposição.
- **Conflito texto × traço:** o PDF não diz o que é cada traço, então hoje isso só sai pela versão Claude.

## Como quero que você atue

- **Faça perguntas antes de assumir.** Traga opções com prós e contras e diga qual recomenda.
- **Separe o tipo de cada ideia:**
  - (a) cabe na versão offline (determinística, sem IA);
  - (b) só na versão Claude;
  - (c) é processo ou padrão de projeto, e não ferramenta.
- **Ajude a priorizar** por esforço × ganho para o verificador.
- **Ao fechar um tema, me entregue um "pedido para a sessão de desenvolvimento":** o que fazer, a evidência disponível, como validar e o que perguntar antes de implementar.

Primeiro tema que quero explorar: [escreva aqui].
