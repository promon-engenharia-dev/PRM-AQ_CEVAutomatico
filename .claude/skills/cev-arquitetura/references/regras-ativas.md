# Estado das regras

A fonte da verdade é o `regras.json`, nos campos `ativa`, `lote` e `status_teste`. Este resumo diz **por que** cada regra está onde está. O detalhe de cada regra (comentário, parâmetros e fontes) está no `CATALOGO_DE_REGRAS.md` §3, §7 e §8.

Validação de base: 40 CEVs de referência de Arquitetura, mais 3 PDFs originais sem CEV.

## Ativas (lote 1)

| Família | Regras | Observação |
|---|---|---|
| PRA (prancha) | PRA-01, 05, 06, 07, 08, 09, 10, 12, 14, 16 | PRA-01 só em documento de edificação, isto é, com TAG `A= … m²`. PRA-05 depende da ficha. PRA-08 confere `/n/` contra a lista de referências da **mesma folha** e ignora "VER NOTA /n/" |
| CAR (carimbo) | CAR-00 a 07, 09, 10, 14 | Só rodam com o modelo de carimbo reconhecido. CAR-03 compara a revisão **e** o número com o nome do arquivo. CAR-02 depende da ficha |
| TAB (tabelas) | TAB-01 a 04, 07 | TAB-01 exige uma tabela só quando o desenho usa o prefixo correspondente |
| KEY (keynotes) | KEY-00, 01, 04 | O vocabulário vem da coluna TAG das tabelas do próprio documento. Exclusões de normas, modelos de equipamento e prefixos de mobiliário ou louças. FL = Folha, não é keynote |
| TAG (ambiente) | TAG-01, 02, 05 | Batem com os comentários "PD?" e "acabamentos?" dos verificadores. TAG-01/02 saem **agrupadas por folha** (um comentário listando os ambientes, com marca em cada TAG) |
| APR (apresentação) | APR-05, 06, 07, 08, 10, 12 | APR-05 é ATENÇÃO, com tolerância de 0,5 mm. APR-06 só nas folhas que usam "ESCALA 1 : N". APR-10 ignora nomes científicos |
| VOC | VOC-01 | 0 achados dentro de um documento. O caso real é **entre documentos** (falta um modo multi-PDF) |
| CON (faltantes) | CON-01, 02, 05 | CON-01/02 são redes de segurança baratas. CON-05 (telhas) só em cobertura de telha |
| LD | LD-00 a 05 | Pegam erros reais de digitação em códigos e títulos. LD-02 é volumosa, porque a lista se repete em cada folha |

Setorização (PRA-12 a 16, `regras/setorizacao.py`) e composição da folha (APR-12/13, TAB-07, CAR-14, `regras/composicao.py`): ver catálogo §19 e §20.

## Inativas e por quê

| Regras | Lote | Motivo |
|---|---|---|
| APR-04 (texto duplicado sobreposto) | 3 | Não aparece na plotagem e ninguém comenta |
| VOC-02 (com × sem acento) | 2 | 34 achados que ninguém comenta. Sem dicionário, não sabe qual forma é a correta |
| CON-03 (descida de água pluvial) | 2 | Dispara em 23 de 30 coberturas, porque a descida costuma ser só um símbolo |
| CON-04 (cota entre eixos) | 2 | Protótipo, amostra pequena e sem confirmação |
| APR-01, 02, 03 (altura de texto, sobreposição) | 2 | Exigem classificar o texto por classe do template (ver decisão Q2-b) |
| PRA-13 e PRA-15 (aguardam aprovação do padrão de setorização), APR-13 (vistas desalinhadas, sem evidência fora do 6110-0005) | 2 | Ver catálogo §19 e §20 |
| PRA-02, 03, 04, 11; CAR-08, 11, 12, 13; KEY-02, 03; TAG-03, 04, 07; VOC-03 | 2 | Heurística de layout ainda não calibrada |
| TAB-05, TAG-06, APR-09 | 3 | Evidência fraca ou contraditória (APR-09: a escala aceitável é juízo do verificador) |
| TAB-06 (célula vazia) | 3 | Exige ler a grade das tabelas pelos vetores de borda |
| REL-01 a 05 (relatórios de texto) | 3 | Família H adiada: não há relatórios verificados como referência |

## Classe do documento (pré-condição de KEY, TAB-01, PRA-01, CON, TAG-01/02, APR-10, CAR-00)

Essas famílias só rodam em prancha (`classes_prancha`). A classe vem do número do documento:
- `…-ARQ-DE-0001` e `…-AQT-DES-0001`: pela sigla de classe;
- numeração Promon `E.<operação>-<assunto>-<seq>`: pelo assunto do PEG0007 (`classe_por_assunto`). AQ2 a AQ5 são desenhos, AQ1 é critério de projeto e AQ8 é especificação.

Os 40 CEVs de referência não têm nenhum número E.*. Até 28/10/2026 essas famílias eram puladas **sem aviso** nos documentos E.*. Ao validar uma regra, teste também nos originais E.*.

## Pendências conhecidas

- **CON-01:** em planta de demolição e corte perspectivado, confirmar se EL é exigido.
- **KEY:** a Tabela de Mobiliário mistura prefixos (MA, MC, MM, MS), e o filtro de prefixo dominante descarta MA, MC e MM do vocabulário. Hoje isso não gera falso positivo, porque a KEY-02 está inativa.

- VOC-01 entre documentos da mesma operação.
- TAB-06 lendo a grade das tabelas pelas bordas vetoriais.
- Família H, quando houver referências.
- CAR-02 e PRA-05 ainda não foram testadas com fichas reais.
