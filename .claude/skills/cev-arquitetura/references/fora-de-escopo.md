# Fora de escopo da versão offline

Estes temas aparecem muito nos CEVs, mas **não** são automatizados por regra determinística. O PDF só informa que há texto e traços, não o que cada traço representa. Além disso, decidir se algo está certo é juízo de quem verifica.

**Todos estão cobertos pela versão Claude** (skill `revisao-assistida-arquitetura`), pelo critério RA indicado. Se um deles passar a ser detectável de forma confiável pelo texto, ele vira proposta de regra offline.

| Tema | Volume nos CEVs | Por que fica fora da versão offline | Versão Claude |
|---|---|---|---|
| "Falta TAG aqui" (janela, porta, calha, revestimento…) | ~90 | Exige saber qual elemento está desenhado no ponto | RA-01 |
| Conflito gráfico texto × traço, cota sobre parede | ~25 | O PDF vetorial não diz o que é cada traço, e o ruído é alto | RA-03 |
| Alinhar ou aproximar título do desenho | ~20 | Delimitar a vista é heurística frágil | RA-04 |
| Cotas faltando (PD, peitoril, calçada, eixo, amarração) | ~40 | Juízo técnico do que precisa ser cotado | RA-02 |
| Representação (shaded, halftone, hatch, profundidade, ortofoto) | ~30 | Juízo gráfico | RA-05 |
| Decisões de projeto (corta-fogo, NBR 9050, módulo, materiais) | ~150 | Juízo de engenharia | RA-08, RA-09, RA-10 |
| Escala "adequada" | — | Os verificadores divergem. Só a **coerência** da escala é verificada offline | RA-11 |
| Coerência entre vistas e notas × desenho | — | Exige interpretar o desenho | RA-06, RA-07 |
| Itens do CheckList sem regra | — | Variados | RA-12 |

Também fora da versão offline:
- itens de modelagem Revit/BIM do CheckList (Levels, Join, IFC, BIM360), que não são verificáveis no PDF em nenhuma das duas versões;
- qualquer uso de IA dentro do `verificador.exe`. A IA entra só pela versão Claude.
