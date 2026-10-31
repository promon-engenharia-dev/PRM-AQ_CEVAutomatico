# Critério de projeto como base de comparação

O critério de projeto da operação define a metodologia construtiva e as regras que os desenhos devem seguir. Pode ser geral da operação ou da disciplina AQ. Na LD, aparece como:
- assunto **AQ1** na numeração Promon `E.<operação>-AQ1-<seq>` (PEG0007: "Critérios de projeto, programa de necessidades…");
- classe **CTP** nas numerações de cliente, por exemplo `…-AQT-CTP-0001`.

## Como encontrar

1. `contexto.json → criterio_projeto`: o preparo procura `*-AQ1-*`, `*CTP*`, `*Crit*rio*` e `*Memorial*Conceitual*` (.pdf/.docx) na pasta do PDF e até 4 pastas acima.
2. **Na LD:** documentos da mesma operação com classe CTP, CP ou MC (`regras.json → revisao_assistida.criterio_projeto.classes_ld`). Com o código em mãos, procure o arquivo nas pastas do projeto.
3. Se houver vários candidatos ou nenhum, **pergunte à usuária** qual usar. Depois, rode o preparo de novo com `--criterio`.

## O que extrair (monte uma tabela de parâmetros antes de revisar)

| Grupo | Exemplos de parâmetro |
|---|---|
| Sistema construtivo | Estrutura (concreto moldado, pré-moldado, metálica), vedação (bloco de concreto 14/19, drywall, painel), módulo |
| Cobertura | Telha, inclinação mínima, calha e rufo, descidas pluviais, platibanda |
| Pé-direito | PD mínimo por tipo de ambiente, entreforro |
| Acabamentos | Piso, parede e teto por tipo de ambiente (áreas molhadas, técnicas, administrativas), rodapé, soleira |
| Esquadrias | Material, dimensões padrão, vergas e contravergas, ventilação permanente |
| Impermeabilização | Sistema por área, altura de subida na parede |
| Acessibilidade e segurança | Exigência de PCD, rotas, normas e ITs adotadas |
| Normas | Lista de normas de referência do critério |

Cite sempre o item e a página do critério na `base` do achado, por exemplo "Critério de Projeto §5.3, p. 12".

## Como comparar

- Para cada parâmetro aplicável à folha, confira o desenho e as tabelas.
  - **Divergente** → ERRO, citando o item.
  - **Não verificável na folha** → não comente, ou comente como ATENÇÃO se for importante.
  - **Atendido** → CORRETO, quando for relevante para a revisão.
- **Folha × critério divergem e o desenho parece mais atual:** use ATENÇÃO ("confirmar se o critério foi revisado").
