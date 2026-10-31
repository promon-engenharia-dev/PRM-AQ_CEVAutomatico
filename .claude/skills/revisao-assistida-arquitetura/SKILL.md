---
name: revisao-assistida-arquitetura
description: Versão Claude do Verificador de Projetos de Arquitetura. Revisa pranchas de Arquitetura (especialidade AQ) em PDF combinando as regras offline da ferramenta com a análise do Claude — TAGs e cotas faltando, conflitos gráficos, coerência entre vistas, notas × desenho, critério de projeto da operação (metodologia construtiva e parâmetros), normas e questões técnicas — e grava tudo no mesmo _CEV.pdf (só vermelho) e relatório. Use quando pedirem para revisar, verificar ou fazer o CEV de um desenho de Arquitetura com o Claude, comparar o desenho com o critério de projeto ou fazer uma revisão técnica assistida.
---

# Revisão assistida de Arquitetura (versão Claude)

Esta é a **versão Claude** do Verificador. A **versão offline** (`python -m verificador` ou `verificador.exe`) continua 100% local e sem IA. As duas versões compartilham:
- o `regras.json`;
- o código de anotação;
- o relatório.

A versão Claude **sempre** roda primeiro todas as regras offline e depois **acrescenta** os achados do Claude. Nunca substitui as regras offline.

**Autorização.** O uso de documentos confidenciais com o Claude está coberto pela licença enterprise da Promon, conforme a usuária confirmou em 28/10/2026. Mesmo assim, não copie trechos dos documentos para o repositório: a pasta de trabalho e o `.revisao.json` ficam ao lado do PDF, fora do Git.

## Fluxo

1. **Preparar.** Rode:
   ```bash
   python -X utf8 ferramentas/preparar_revisao.py <arquivo.pdf> [--criterio <criterio.pdf|.docx>] [--ld <LD.xlsx>]
   ```
   Isso cria a pasta `<nome>_revisao/` com:
   - `contexto.json`: carimbo, ficha deduzida, operação, LD, folhas e recortes com a posição de cada um em mm, critério de projeto e avisos;
   - `offline.json`: o que as regras offline já apontaram. **Não repita esses achados.**
   - `folha_NN.png` (visão geral) e `folha_NN_LxCy.png` (recortes ampliados, com 8% de sobreposição);
   - `folha_NN_texto.tsv`: cada linha de texto com a caixa em mm (folha como exibida, origem no canto superior esquerdo) e o corpo em pt;
   - `criterio_projeto.txt`: quando o critério de projeto é encontrado.
2. **Critério de projeto.** Se `contexto.json` não trouxer `criterio_projeto`, procure nesta ordem:
   - na LD, um documento da operação com classe CTP/CP/MC da disciplina AQ (ou geral);
   - nas pastas do projeto;
   - perguntando à usuária.

   Sem o critério, a revisão segue, mas RA-08 não é avaliada; avise no resumo. Para extrair os parâmetros, veja `references/criterio-de-projeto.md`.
3. **Ler a folha.**
   - Comece pela visão geral para entender a organização: vistas, tabelas, notas, carimbo.
   - Depois leia **todos** os recortes ampliados.
   - Use o `texto.tsv` para confirmar textos e pegar a âncora exata.
   - Não conclua nada a partir de texto que não conseguiu ler: na dúvida, use ATENÇÃO e diga o que confirmar.
4. **Revisar** pelos critérios RA-01 a RA-12 (`references/criterios.md`). A lista oficial e os nomes ficam em `regras.json → revisao_assistida.criterios`. Inclua:
   - os itens "fora de escopo" da versão offline;
   - os parâmetros do critério de projeto;
   - as questões técnicas (normas, solução de projeto, coerência entre vistas).
5. **Escrever** `<nome>.revisao.json` na pasta de trabalho, no formato de `references/formato-json.md`.
   - Severidades: **ERRO** = corrigir, **ATENCAO** = o verificador confirma, **CORRETO** = conferido. CORRETO aparece só no relatório, nunca no PDF.
   - Registre como CORRETO as conferências relevantes que passaram. Isso mostra o que foi checado.
6. **Gravar** com a ferramenta, para gerar o mesmo `_CEV.pdf`, relatório e CSV da versão offline:
   ```bash
   python -X utf8 -m verificador --sem-formulario --revisao <pasta>/<nome>.revisao.json [--ld ...] [--csv] <arquivo.pdf>
   ```
   Confira os avisos na saída (âncora não encontrada, critério inexistente) e corrija o JSON.
7. **Resumir para a usuária.** Informe:
   - os números por severidade e origem;
   - os achados técnicos mais importantes;
   - o que não foi possível avaliar (critério ausente, texto ilegível);
   - as **propostas de alinhamento** (próxima seção).

## Alinhamento entre as versões (obrigatório)

- **Achado mecânico vira proposta offline.** Se um achado do Claude puder ser detectado de forma determinística pelo texto do PDF, por exemplo uma TAG sem linha na tabela que a KEY-01 deixou passar, ele também é uma **falha ou lacuna da versão offline**.
  - Registre-o no resumo como "proposta de regra ou correção offline".
  - Siga a skill `cev-arquitetura` para corrigir ou criar a regra, sempre com aprovação da usuária.
- **Critério novo:** entra primeiro em `regras.json → revisao_assistida.criterios` e em `references/criterios.md`.
- **Mudança no `regras.json`, no catálogo ou nas regras offline:** verifique se esta skill continua coerente.
- **Verificação:** rode `python -X utf8 ferramentas/checar_alinhamento.py` antes de encerrar qualquer mudança. Ele deve passar sem erros.

## Escrita dos comentários

- **Português técnico, curto e imperativo na ação.** `comentario` diz o que está errado e onde. `acao` diz o que fazer, com o porquê quando for técnico. `base` cita a fonte: item do critério de projeto, norma, nota da folha, CheckList AQ, PEG.
- **Âncora:** o texto mais curto e único que aparece no ponto (TAG, nome do ambiente, cota). Sem texto no ponto, use `retangulo_mm`, medido pelo `retangulo_mm` do recorte.
- **Questões técnicas:** são permitidas, desde que fundamentadas. Prefira ATENÇÃO, a menos que a divergência com o critério ou a norma seja objetiva.
- **Não invente:** valores de norma ou do critério só com a fonte em mãos. Se não tiver, escreva "confirmar em …".
