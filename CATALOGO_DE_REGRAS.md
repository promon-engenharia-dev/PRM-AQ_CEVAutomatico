# Catálogo de Regras — Verificador de Projetos · Arquitetura (CEV automática)

> Escopo: disciplina de **Arquitetura** (especialidade AQ). Outras disciplinas exigiriam catálogo próprio.

**Versão:** 0.3 — lote 1 implementado e testado contra os 40 CEVs (ver §6); regras do lote 1 ativas **em teste**
**Data:** 23/10/2026
**Parâmetros:** todos em [`regras.json`](regras.json) (chave = código da regra). Este documento é a explicação humana; o JSON é a fonte dos valores.

---

## 1. O que a inspeção das referências confirmou e o que ela muda

Base inspecionada: 40 CEVs (`referencias/CEV-Referencias/...`), 1.204 caixas de texto com comentário, 1.149 delas em vermelho (≈ 680 textos distintos), o `CheckList Arquitetura.xlsx`, o PEG0005 rev. 5.0 e o PEG0007 rev. 8.0.

### 1.1 Confirmado

| Item do briefing | Evidência |
|---|---|
| Caixa de texto explicativo: `/FreeText`, `/Subj (Texto Explicativo)`, `/IT /FreeTextCallout`, `/C [1 1 1]`, `/LE /OpenArrow` | 601 ocorrências, todas com esse padrão |
| `/DA (1 0 0 rg /F1 10 Tf)` | padrão mais frequente (537); o 2º é `.937 .325 .314 rg` (523, vermelho “Acrobat”) |
| `/DS (font-family:Arial Narrow;font-size:10pt;color:#FF0000;)` | 952 ocorrências (a variante `ArialNarrow` sem espaço aparece 107 vezes) |
| Seta: `/Line`, `/Subj (Seta)`, `/IT /LineArrow`, vermelho | 287 setas; 253 vermelhas |
| Armadilha AutoCAD SHX | 7 dos 40 arquivos têm de 212 a 1.926 anotações `/Square` com `/T (AutoCAD SHX Text)`. Elas são filtradas pelo autor. |

### 1.2 Ajustes ao briefing (pedem sua decisão; ver §5)

1. **O código de cores é o item 6.4.2 do PEG0005 rev. 5.0, não o 6.1.5.** O texto é o mesmo. O item **7.3** também associa ferramentas a cores: *Amarela = “Linha”; Vermelha = “Seta” + “Chamada”; Azul = “Retângulo” + “Nota”; Verde = “Oval” + “Carimbo”*.
2. ✅ *Resolvido (Q1): o trecho é marcado com **nuvem de revisão vermelha** (padrão dos seus CEVs: `/Polygon`, `/Subj (Nuvem)`, `/IT /PolygonCloud`, `/C [1 0 0]`, `/BE << /S /C /I 1 >>`, sem preenchimento; 25 nuvens vermelhas nos CEVs), ou apenas pela ponta de seta da caixa de texto. Sem Highlight e sem Linha translúcida.* Contexto original: **nos seus CEVs a “Linha” translúcida (W 6, opacidade 0,4) é quase sempre AMARELA**, ou seja, “conforme”: são cerca de 3.500 linhas amarelas contra cerca de 570 vermelhas. **O Realce (`/Highlight`) aparece 181 vezes, e sempre em âmbar `[1 0.757 0]`. Não há nenhum realce vermelho nos 40 CEVs.** Um realce vermelho translúcido pode ser lido como amarelo por quem bate o olho, e pelo item 7.3 do PEG o vermelho é a Seta mais a Chamada. → **Pergunta Q1.**
3. *Com Q1, a seta passa a ser a ponta (`/LE /OpenArrow`) da própria caixa de texto explicativo; a anotação `/Line` “Seta” separada fica desativada no JSON.* **Seta:** nos seus CEVs, `/BS` costuma estar ausente (222 de 253 setas vermelhas, largura padrão 1); `/W 2` aparece em 31. Quanto a `/LE`, metade das setas usa `[/OpenArrow /OpenArrow]` (143) e metade `[/None /OpenArrow]` (144). Mantive o seu padrão (`W 2`, duas pontas), que é configurável.
4. **Nomenclatura do CEV:** o PEG0005 (7.3 e 6.2) fala em “-CV1/-CV2” e “CEV1/CEV2”, e os arquivos usam `_CEV`, `_CEV1` e `_CEV2`. Proposta: tratar como “já é CEV” qualquer nome que case com `_CEV\d*$`; a saída de `X_CEV2.pdf` vira `X_CEV2_auto.pdf`.
5. **O conteúdo da página de um CEV não está limpo.** Nos CEVs de revisão (ex.: `3-N-T012-0503-B-ARQ-DE-0001_R2_CEV`), comentários de rodadas anteriores estão **achatados** no conteúdo (texto Arial Narrow 10 pt), junto com o carimbo “Cópia de Verificação / AÇÃO / VISTO” (Calibri-Bold) e o texto de assinatura digital (“Assinado digitalmente por …”). Sem filtro, a ferramenta comentaria os próprios comentários. Os filtros estão em `regras.json → filtros.conteudo`.
6. **Existem pelo menos três modelos de carimbo** e cada um precisa de mapeamento próprio:
   - **Promon/RUMO (3-N-T012…):** rótulos em PT (`NÚMERO DESENHO:`, `REV:`, `FOLHA:`, `ESCALA:`, `TÍTULO:`, `ARQ. MAGNÉTICO:`, bloco PROJETO/DESENHO/VERIFICADO/APROVADO, histórico REVISÃO/DATA/DESCRIÇÃO/EXECUTADO/VERIFICADO/APROVADO);
   - **1-P-T015…:** mesmos rótulos, mas a **página é girada 90°** (texto com direção vertical);
   - **6110/7610/7210 (cliente estrangeiro):** rótulos em inglês e **itálicos** (`Rev.`, `Date`, `Dwn.`, `Ver.`, `Approv.`, `Description`, `Issued`).
   As regras de carimbo só rodam quando um modelo é reconhecido. Caso contrário, saem um único ATENÇÃO “carimbo não reconhecido” e nada mais.
7. **Revisão numérica × alfabética:** o PEG0007 9.4.4 manda `0, A, B, C…` e admite numeração numérica se ela constar do procedimento da operação. As suas referências têm os dois casos (`_R2` com REV “2”; `-P_A`). Proposta: um campo `esquema_revisao` na ficha (`"alfabetico"` | `"numerico"`).
8. **Altura de texto 2,0–4,0 mm vai gerar ruído em massa.** O tamanho no PDF (pt) não é a altura do Revit. A altura de maiúscula da Arial ≈ 0,716 × corpo, e com isso as medições dão:
   - tags/keynotes 6,0 pt ≈ **1,5 mm**;
   - cotas 8,6 pt ≈ 2,2 mm;
   - títulos de vista 17,2 pt ≈ 4,3 mm;
   - bolhas de eixo 19,3 pt ≈ 4,9 mm;
   - notas do modelo 6110 5,0 pt ≈ 1,3 mm.

   O texto mais frequente da folha (1,5 mm) ficaria fora da faixa, e os seus próprios comentários pedem “texto 1,5 mm Arial”, “1.2 Arial Narrow” e “texto 2.0 mm”. → **Pergunta Q2.**
9. **Escala “fora do conjunto usual”:** você criticou 1:75 em `6110-…-0010` (“PORQUE FICOU NA 1:75?”, 9×) e sugeriu 1:75 em `7610-…-0005` (“vale testar a escala 1:75”). Escala aceitável é juízo do verificador. Proponho no lugar **coerência**: vista sem escala, escala da vista ≠ carimbo, formato da escala.
10. **Folha x/y:** o seu comentário “01/04 DEVE CORRESPONDER AO TOTAL DO PROJETO” mostra que **y é o total de folhas do documento**, que vem da ficha, e não o número de páginas do PDF (um PDF pode conter só parte das folhas).
11. **O checklist é de modelagem Revit (BIM).** A maior parte dos itens (Levels, Join, Properties, IFC, BIM360) não é verificável no PDF. Usei apenas as seções FOLHAS (B79–B87) e PLANTA/CORTES/COBERTURA, na parte que aparece impressa.
12. **Relatórios (família H): não há evidência nos CEVs.** Os dois relatórios de referência (`…ENG-MF-0001`, `…PLA-PL-0001`) têm só 3 caixas de texto, todas sobre carimbo/revisão. A família H fica sem validação possível. → **Pergunta Q4.**

### 1.3 Validação preliminar da família D (keynotes)

Fiz um teste rápido e descartável (não é a ferramenta) em todos os 40 CEVs. O vocabulário foi montado a partir da coluna `TAG` das tabelas do próprio documento.

- **Funciona** nos modelos 3-N-T012, 6110 e 7610: são de 9 a 63 códigos por documento, extraídos sem erro.
- **Falha hoje** nos 1-P-T015 (vocabulário de 1 código) porque a página é girada. Isso tem correção conhecida: ler o texto na orientação dele.
- **Falsos positivos encontrados**, que já estão nas exclusões do JSON:
  - `GA30` e `GA110` são modelo de compressor (“GA30-45”);
  - `NR24` é norma;
  - `FL01…FL07` aparecem em 9 documentos e não estão em nenhuma tabela. *Resolvido (Q3): FL = Folha.* O prefixo sai do vocabulário de keynotes e passa a ser usado pela nova regra PRA-11;
  - `TQ01` e `DV10` estão fora das tabelas em vários documentos.
- **“Linha de tabela sem uso” é dominada por peças sanitárias e mobiliário** (`HD01…HD28`, `MS10…`, `PI07`). Isso é coerente com o seu comentário “Não precisa colocar TAG nas instalações sanitárias”. Esses prefixos ficam excluídos.
- **Cobertura dos seus comentários de keynote:** a maioria (`CP41`, `TQ02`, `RE30?`, `TE30`, `RE34?`, `REXX??`) significa “**falta TAG aqui**” ou “TAG errada aqui”. Isso exige entender o desenho e **não é automatizável** com segurança. A regra D acerta os casos do tipo “código sem linha na tabela”, como “Não há o RE21 nas tabelas de quantidades” (`1302-0004`) e `CP02` (`1304-0002_R2`).
- **Conclusão:** a regra é confiável, mas de alcance modesto.

---

## 2. Convenções deste catálogo

- **Severidade:** `ERRO` = divergência objetiva, certeza alta · `ATENÇÃO` = heurística, o verificador confirma.
- **Lote:**
  - **1** = regra determinística, entra primeiro;
  - **2** = depende de heurística de layout e precisa de calibração contra os CEVs antes de entrar;
  - **3** = candidata fraca ou sem evidência, só se você quiser.
- **Fontes:** `CK` = CheckList Arquitetura.xlsx (célula) · `PEG5` = PEG0005 · `PEG7` = PEG0007 · `CEV` = seus comentários (nº de ocorrências / nº de arquivos).
- **Texto do comentário:** `{…}` é substituído em tempo de execução. Todo comentário começa com uma TAG de verificação `CV-AQ-nnn — ` (Q5): `AQ` = especialidade (PEG0007 9.2, configurável) e `nnn` = índice sequencial do comentário no documento (folha 1 → última, de cima para baixo e da esquerda para a direita). O código da regra (`[CAR-03]` nas tabelas abaixo) **não** aparece na caixa: ele vai para o CSV e para o campo oculto `/NM` da anotação, ligando cada `CV-AQ-nnn` à regra que o gerou.
- **Escopo de documento:** regras de prancha (A, C, D, G) avaliam o **documento inteiro** (todas as páginas do PDF), porque as vistas e as tabelas costumam estar distribuídas entre folhas.

---

## 3. Catálogo

### A. Prancha / folha — `PRA`

| Código | Regra | Sev. | Parâmetro (`regras.json`) | Comentário na caixa vermelha | Fonte | Lote |
|---|---|---|---|---|---|---|
| PRA-01 | Documento de desenho (classe DE) sem um dos blocos-título obrigatórios: PLANTA-CHAVE, NOTAS GERAIS, DOCUMENTOS DE REFERÊNCIA | ERRO | `blocos_obrigatorios` (rótulo + variantes) | `[PRA-01] Incluir {bloco} na folha.` | CK B81, B82, B84 · CEV (“usar planta chave existente”, “nao esquecer de incluir a nota 2”) | 1 |
| PRA-02 | Legenda de fechamentos ausente quando há tabela de fechamentos | ATENÇÃO | `legenda.rotulos`, `legenda.so_se_tabela` | `[PRA-02] Incluir Legenda de Fechamentos.` | CK B83 · CEV (“O que é essa diferença de hatch? … deve ser sinalizada na legenda”, “nao foi encontrado no desenho … suprimir essa legenda”) | 2 |
| PRA-03 | Página com PLANTA BAIXA sem indicação de norte (texto `NV`/`NP`/`N`/“NORTE” na página) | ATENÇÃO | `norte.marcadores_texto` | `[PRA-03] Incluir orientação do Norte junto à planta baixa.` | CK B85 · CEV “INCLUIR ORIENTAÇÃO DO NORTE” (7/1), “nao esquecer o norte do projeto” (1/1) | 2 |
| PRA-04 | Vistas mínimas ausentes no documento (Planta Baixa, Planta de Cobertura, ≥ 2 Cortes, Elevações, Perspectiva) | ATENÇÃO | `vistas_obrigatorias` (padrão de título + quantidade mínima) | `[PRA-04] Não encontrei {vista} no documento. Confirmar se está em outro documento da LD.` | CK B79, B86 · CEV “INCLUIR VISTA 3D PERSPECTIVA EXPLODIDA” (1/1) | 2 |
| PRA-05 | Numeração de folha: total (y) ≠ total da ficha | ERRO | `folha.regex` | `[PRA-05] Folha {x}/{y}: o total deve corresponder ao total de folhas do documento ({total_ficha}).` | CEV “01/04 DEVE CORRESPONDER AO TOTAL DO PROJETO” (2/1) | 1 |
| PRA-06 | Numeração de folha: x > y, x repetido ou salto entre páginas do mesmo PDF | ERRO | `folha.regex` | `[PRA-06] Numeração de folha incoerente: {detalhe}.` | CEV “FL. 2” (3/1) | 1 |
| PRA-07 | Formato da numeração diferente do padrão do modelo (ex.: `1` em vez de `01 / 02`) | ATENÇÃO | `folha.formato_padrao` | `[PRA-07] Ajustar formato da folha para "{formato}".` | CEV “Não seria "01" ou "FL.1"??” (4/1) | 1 |
| PRA-08 | Referência `/n/` citada em nota ou desenho sem item `n` na lista de Documentos de Referência | ERRO | `referencias.regex_citacao`, `referencias.regex_item` | `[PRA-08] Referência /{n}/ citada, mas não consta na lista de Documentos de Referência.` | CEV “Se foi citado em nota precisa estar listado nos documentos de referência” (1/1), “VER REFERÊNCIA /X/” (12/2) | 1 |
| PRA-09 | Mesmo código de documento repetido em dois itens da lista de referências | ERRO | `referencias.regex_codigo_documento` | `[PRA-09] Itens {i} e {j} dos Documentos de Referência têm o mesmo código ({codigo}).` | CEV “documentos de referência apresenta os itens 06 e 07 com o mesmo código” (1/1) | 1 |
| PRA-11 | Remissão a folha `FLnn` com nn maior que o total de folhas do documento (FL = Folha, Q3) | ATENÇÃO | `remissao_folha.regex` | `[PRA-11] Remissão a {codigo}, mas o documento tem {total} folha(s).` | Q3 · nos CEVs o maior FLnn é sempre ≤ nº de folhas (ex.: `7610-0003`: FL01…FL07 em 7 folhas; `6110-0010`: FL01…FL04 em 4) | 2 |
| PRA-10 | Texto de espaço reservado não preenchido (`XXX`, `xx m`, `/X/`, `REXX`, `A DEFINIR`) | ATENÇÃO | `placeholders.regex` | `[PRA-10] Texto provisório "{texto}" — preencher ou confirmar se deve permanecer.` | CEV “Georreferenciamento? N (Y) = xx m” (1/1), “REXX??” (6/1) | 1 |

### B. Carimbo — `CAR`

Pré-condição de todas: carimbo reconhecido por um modelo de `carimbo.modelos`. Os campos comparados com a ficha só rodam se a ficha existir.

| Código | Regra | Sev. | Parâmetro | Comentário na caixa vermelha | Fonte | Lote |
|---|---|---|---|---|---|---|
| CAR-00 | Carimbo não reconhecido por nenhum modelo (as demais CAR não rodam) | ATENÇÃO | `carimbo.modelos` | `[CAR-00] Carimbo não reconhecido — campos do carimbo não verificados automaticamente.` | — | 1 |
| CAR-01 | Campo obrigatório vazio (número, revisão, folha, escala, título, executado/desenho, verificado, aprovado, data) | ERRO | `carimbo.campos_obrigatorios` | `[CAR-01] Preencher campo "{campo}" do carimbo.` | PEG7 9.4.3 · CEV “preencher nome usuário autodesk” (2/2) | 1 |
| CAR-02 | Campo do carimbo diverge da ficha (número, revisão, descrição, data, título, cliente/operação, executado, verificado, aprovado, total de folhas) | ERRO | `carimbo.comparacao` (normalização: caixa, espaços, acentos só para comparar) | `[CAR-02] {campo}: "{valor_pdf}" — esperado "{valor_ficha}".` | CK B87 · CEV datas “06/02/2026”, “12/12/2025” (13/3); siglas “JVM”, “ACFC”; “O título deve estar igual à LD”; “atulizar o numero documento”; “E.RUMO013.3-AQ3-04001” | 1 |
| CAR-03 | Revisão do carimbo ≠ revisão no nome do arquivo (`_R2`, `-P_A`) | ERRO | `nome_arquivo.regex_revisao` | `[CAR-03] Revisão do carimbo ({rev_carimbo}) difere da revisão no nome do arquivo ({rev_arquivo}).` | CEV “_R0” (1/1) | 1 |
| CAR-04 | Revisão do carimbo ≠ última linha do histórico de revisões | ERRO | — | `[CAR-04] Revisão do carimbo ({rev_carimbo}) difere da última revisão do histórico ({rev_historico}).` | PEG7 9.4.4 | 1 |
| CAR-05 | Histórico fora de sequência (salto, repetição) ou com datas decrescentes | ERRO | `revisao.sequencias` | `[CAR-05] Histórico de revisões fora de sequência: {detalhe}.` | PEG7 9.4.4 | 1 |
| CAR-06 | Esquema de revisão diferente do declarado na ficha (numérico × alfabético) ou misto no histórico | ATENÇÃO | `revisao.esquemas` | `[CAR-06] Revisão "{rev}" fora do esquema {esquema} adotado na operação (PEG0007 9.4.4).` | PEG7 9.4.4 · CEV “Padrão de emissões atualizado iremos subir como R1” | 1 |
| CAR-07 | Rev. 0 com descrição ≠ “EMISSÃO INICIAL”, ou rev. > 0 com “EMISSÃO INICIAL” | ERRO | `revisao.descricao_rev0` | `[CAR-07] Descrição da revisão {rev}: usar "EMISSÃO INICIAL" somente na revisão 0.` | CK B87 · PEG7 9.4.5 · CEV “EMISSÃO INICIAL” (1/1), “Ajustar ortografia - "EMISSÃO"” (1/1) | 1 |
| CAR-08 | Descrição da revisão > 0 vazia ou genérica (lista configurável; ex.: “REVISÃO”, “-”) | ATENÇÃO | `revisao.descricoes_genericas` | `[CAR-08] Descrição da revisão {rev} deve informar a modificação ocorrida (PEG0007 9.4.5).` | PEG7 9.4.5 | 2 |
| CAR-09 | Campo “ARQ. MAGNÉTICO” ≠ número do documento + revisão | ERRO | `carimbo.arquivo_magnetico.regex` | `[CAR-09] Arquivo magnético "{valor}" não corresponde a {numero}_R{rev}.` | modelo Promon (campo presente em 3-N-T012…) | 1 |
| CAR-10 | Mesma sigla em Executado e Verificado na mesma revisão | ERRO | — | `[CAR-10] Verificador não pode ser o executante do documento (PEG0005 6.3).` | PEG5 6.3 · PEG7 9.4.3 | 1 |
| CAR-11 | Siglas/datas do bloco PROJETO/DESENHO/VERIFICADO/APROVADO ≠ última linha do histórico | ATENÇÃO | — | `[CAR-11] {campo} do carimbo ({valor_bloco}) difere da última revisão do histórico ({valor_historico}).` | modelo Promon | 2 |
| CAR-12 | Núcleo do título mudou em relação à ficha da revisão anterior | ATENÇÃO | `titulo.similaridade_minima` | `[CAR-12] Título alterado em relação à revisão anterior — mudança de título só para complementação (PEG0007 9.4.8).` | PEG7 9.4.8 | 2 |
| CAR-13 | Linha de título do carimbo (ex.: “PLANTAS E CORTES”) não corresponde às vistas presentes na folha | ATENÇÃO | `titulo.mapa_vistas` | `[CAR-13] Título "{titulo}" deve corresponder ao conteúdo da folha (vistas encontradas: {vistas}).` | CEV “PLANTAS E CORTES - deve corresponder ao conteudo da folha” (2/1), “ELEVACOES E PERSPECTIVAS - …” (2/1), “PLANTA BAIXA, PLANTA DE COBERTURA E PERSPECTIVA?” (1/1) | 2 |

### C. Tabelas — `TAB`

Uma tabela é reconhecida pelo título (`TABELA DE …`, `QUADRO DE …`) e pelo cabeçalho de colunas.

| Código | Regra | Sev. | Parâmetro | Comentário na caixa vermelha | Fonte | Lote |
|---|---|---|---|---|---|---|
| TAB-01 | Tabela obrigatória ausente no documento (lista do checklist; as “se houver” só são exigidas quando um keynote do prefixo correspondente aparece no desenho) | ATENÇÃO | `tabelas.obrigatorias`, `tabelas.condicionais` | `[TAB-01] Incluir {tabela}.` | CK B80 · CEV “TABELA DE JANELAS??” (1/1), “tabelas de acabamentos” (1/1) | 1 |
| TAB-02 | Tabela com título e cabeçalho, mas sem linhas | ERRO | — | `[TAB-02] {tabela} está vazia.` | pedido do briefing (sem ocorrência nos CEVs) | 1 |
| TAB-03 | Quadro de Áreas sem as linhas ÁREA CONSTRUÍDA e ÁREA COBERTA | ERRO | `tabelas.quadro_areas.linhas_obrigatorias` | `[TAB-03] Quadro de Áreas deve conter ÁREA CONSTRUÍDA e ÁREA COBERTA.` | CK B80 · CEV “Rever quadro de áreas, colocar ÁREA CONSTRUIDA ÁREA COBERTA” (1/1) | 1 |
| TAB-04 | Unidade repetida nas células quando o cabeçalho já tem a unidade (ex.: “174,84 m²” sob “ÁREA (m²)”) | ERRO | `tabelas.unidades` | `[TAB-04] Suprimir "{unidade}" após o valor — a unidade já está indicada no cabeçalho.` | CEV “Suprimir "m²" após o valor numérico, já foi indicado no título” e variantes (9/7) | 1 |
| TAB-05 | Ordem das tabelas na folha diferente da ordem do checklist | ATENÇÃO | `tabelas.ordem` | `[TAB-05] Posicionar as tabelas na ordem do Checklist de AQ ({posicao_esperada}ª: {tabela}).` | CK B80 · CEV “Colocar as Tabelas na folha na mesma ordem que indicado no Checklist de AQ” (1/1) | 3 |

### D. Cruzamento tabela × desenho (keynotes) — `KEY`

Vocabulário válido = códigos da coluna `TAG` das tabelas do próprio documento, cada código ligado ao **prefixo** e à tabela de origem. Um código é `[A-Z]{2,3}\d{2,3}` (ex.: TE30, RE34, PI46, JAM22, PAV04, GA110). **Pré-condição:** com menos de `vocabulario_minimo` códigos (5) a família D não roda e sai uma única ATENÇÃO.

| Código | Regra | Sev. | Parâmetro | Comentário na caixa vermelha | Fonte | Lote |
|---|---|---|---|---|---|---|
| KEY-00 | Vocabulário insuficiente — tabelas de keynote não identificadas | ATENÇÃO | `vocabulario_minimo` | `[KEY-00] Tabelas de keynote não identificadas — cruzamento tabela × desenho não realizado.` | — | 1 |
| KEY-01 | Código usado no desenho cujo **prefixo existe** no vocabulário, mas sem linha na tabela | ERRO | `exclusoes` | `[KEY-01] {codigo} não consta na {tabela_do_prefixo}.` | CEV “Não há o RE21 nas tabelas de quantidades” (1/1), “Não está na Tabela de acabamentos” (1/1), “CP02?” | 1 |
| KEY-02 | Código com formato de keynote cujo **prefixo não existe** em nenhuma tabela | ATENÇÃO | `exclusoes` (normas, modelos de equipamento, prefixos), `contexto_exclusao` | `[KEY-02] {codigo} não pertence a nenhuma tabela do documento — confirmar se é keynote.` | briefing (nunca ERRO) | 2 |
| KEY-03 | Linha de tabela cujo código não aparece em nenhum desenho do documento | ATENÇÃO | `prefixos_sem_tag_no_desenho` (HD, MS…) | `[KEY-03] {codigo} consta na {tabela}, mas não foi encontrado nos desenhos.` | CEV “nao foi encontrado no desenho, se nao tiver, suprimir” (1/1) | 2 |
| KEY-04 | Mesmo código em duas linhas (na mesma tabela ou em tabelas diferentes) com descrições diferentes | ERRO | `normalizacao_descricao` | `[KEY-04] {codigo} aparece com descrições diferentes: "{desc1}" × "{desc2}".` | CEV “TAG duplicada” (1/1), “duplicado?” (2/2) | 1 |

### E. TAGs de ambiente e cotas — `TAG`

Uma TAG de ambiente é reconhecida como um agrupamento espacial: nome do ambiente + `A= … m²` + `PD= … m` + 3 códigos de acabamento (piso/parede/teto), como no modelo Promon.

| Código | Regra | Sev. | Parâmetro | Comentário na caixa vermelha | Fonte | Lote |
|---|---|---|---|---|---|---|
| TAG-01 | TAG de ambiente com `A=` mas sem `PD=` (ou o contrário) | ERRO | `tag_ambiente.regex_area`, `regex_pd`, `raio_agrupamento_mm` | `[TAG-01] TAG do ambiente {ambiente}: falta {item}.` | CK B26, B29 · CEV “PD?” (12/1), “PD = ??” (2/1), “CADE AREA??” (1/1), “COTA P.D.” | 2 |
| TAG-02 | TAG de ambiente com menos de 3 códigos de acabamento | ATENÇÃO | `tag_ambiente.acabamentos_minimos` | `[TAG-02] TAG do ambiente {ambiente} deve indicar os 3 acabamentos (piso, parede, teto).` | CK B26, B28 · CEV “TAG do ambiente com os acabamentos” (1/1), “acab??” (2/1), “Revestimento de teto?” (2/1) | 2 |
| TAG-03 | Ambiente da planta ausente do Quadro de Ambientes | ERRO | `tag_ambiente.normalizacao_nome` | `[TAG-03] Ambiente "{ambiente}" não consta no Quadro de Ambientes.` | briefing · CK B80 | 2 |
| TAG-04 | Área da TAG ≠ área do mesmo ambiente no Quadro de Ambientes | ERRO | `tag_ambiente.tolerancia_area_m2` | `[TAG-04] Área do ambiente {ambiente}: TAG {area_tag} m² × Quadro {area_quadro} m².` | CEV “Esse valor esta correto?? 28,18 * 6,20 = 174,77 m²”, “Muita diferença entre as áreas nao?”, “NÃO BATE COM m² ÁREA CONSTRUIDA” | 2 |
| TAG-05 | Cota de nível fora do formato do projeto (prefixo `EL.`, casas decimais) ou formatos misturados no documento | ATENÇÃO | `cota_nivel.regex_valida`, `cota_nivel.casas_decimais` | `[TAG-05] Cota de nível "{texto}" fora do padrão "{exemplo}".` | briefing · CEV “EL. 0,00 REF.” (7/1), “720,00 M” | 1 |
| TAG-06 | Cota de nível sem qualificador quando o padrão exige (`(ACAB.)`, `(CALÇADA)`, etc.) | ATENÇÃO | `cota_nivel.qualificadores` | `[TAG-06] Cota de nível sem qualificador — indicar (ACAB.), (CALÇADA) ou equivalente.` | CK B30, B31 · CEV “COTA DE NIVEL ACAB?” (1/1), “Nivel acabado?” (1/1) | 3 |
| TAG-07 | Cota com valor “quebrado” (decimal ou fora do módulo; ex.: 191,5 · 98,5 · 399) — incluída por Q6 como item a validar pelo verificador final | ATENÇÃO | `cotas.modulo_cm`, `cotas.aceitar_decimais` | `[TAG-07] Cota com valor quebrado ({valor}) — a validar pelo verificador.` | Q6 · CEV “Esse valor é quebrado mesmo?” (12/2), “Verificar porque os valores estão quebrados” (4/2), “ajustar para ficar 400” (3/1), “números inteiros ou múltiplos de 10cm” (2/2) | 2 |

### F. Apresentação — `APR`

| Código | Regra | Sev. | Parâmetro | Comentário na caixa vermelha | Fonte | Lote |
|---|---|---|---|---|---|---|
| APR-01 | Altura de texto fora de {1,5; 2,0} mm no desenho, ou acima de 4,0 mm no carimbo (Q2), medida pela altura de maiúscula na escala 100%, tolerância ± 0,2 mm. **Um comentário por folha e por altura**, apontando um exemplo e informando a quantidade, para não poluir | ATENÇÃO | `altura_texto.*` — **ver §5, Q2-b** | `[APR-01] {n} texto(s) com altura {altura} mm — padrão: 1,5 ou 2,0 mm (ex.: "{exemplo}").` | Q2 · CEV “Favor ajustar para o texto 2.0 mm” (3/1), “texto - 1,5mm arial” (1/1), “1.2 Arial Narrow” (1/1) | 2 |
| APR-02 | Dentro de um mesmo grupo (mesma tabela, mesmo bloco de notas, mesmo tipo de TAG) uma altura destoa da mediana do grupo | ATENÇÃO | `altura_destoante.desvio_relativo` | `[APR-02] Texto com altura diferente do restante do grupo ({altura} mm × {mediana} mm).` | CEV “Todos os textos precisam estar no mesmo tamanho dos textos das cotas” (3/1), “foi alterada a configuração das tabelas? … deixar o texto do mesmo tamanho” (1/1) | 2 |
| APR-03 | Dois textos diferentes com sobreposição de caixas acima do limiar | ATENÇÃO | `sobreposicao.area_minima_rel` | `[APR-03] Textos sobrepostos — ajustar para evitar conflito gráfico.` | CEV “conflito gráfico”/“sobreposição” e variantes (29/11; a maioria é texto × traço, que não é detectável) | 2 |
| APR-04 | Mesmo texto duplicado na mesma posição (TAG empilhada) | ATENÇÃO | `duplicado.distancia_max_mm` | `[APR-04] Texto "{texto}" duplicado na mesma posição.` | observado em `0503-0001_R2` (“(ACAB.)” 2× nas mesmas coordenadas) · CEV “TAG duplicada” | 1 |
| APR-05 | Texto cortado pela borda da folha (caixa fora do `mediabox`) | ERRO | `borda.margem_mm` | `[APR-05] Texto cortado pela borda da folha.` | briefing (sem ocorrência nos CEVs) | 1 |
| APR-06 | Título de vista sem linha de escala logo abaixo; para perspectiva/3D o esperado é “SEM ESCALA” | ERRO (planta/corte/elevação) · ATENÇÃO (perspectiva) | `vistas.regex_titulo`, `vistas.distancia_escala_mm` | `[APR-06] Indicar a escala da vista ({vista}).` / `[APR-06] Indicar "SEM ESCALA" na perspectiva.` | CEV “SEM ESCALA” (8/7), “Colocar a escala do desenho aqui - Planta 1 - esc. xxx” (3/1) | 1 |
| APR-07 | Escala do carimbo ≠ escala única das vistas; ou vistas com escalas diferentes e carimbo sem “INDICADA” | ERRO | `escala.valor_multiplas` | `[APR-07] Escala do carimbo ({escala_carimbo}) não corresponde às vistas ({escalas_vistas}).` | CEV “INDICADA” (1/1) | 1 |
| APR-08 | Escala fora do formato `1 : N` (ex.: `1:100`, `ESC 1/100`) | ATENÇÃO | `escala.formato` | `[APR-08] Escrever a escala no formato "1 : {n}".` | CEV “SE ESCREVE 1 : XXX” (2/1) | 1 |
| APR-09 | Escala fora do conjunto usual | ATENÇÃO | `escala.conjunto_usual` | `[APR-09] Escala 1 : {n} fora do conjunto usual — confirmar.` | briefing · CEV contraditório (ver §1.2-9) | 3 |
| APR-10 | Texto em fonte itálica fora da área do carimbo (o modelo 6110/7610 usa itálico no carimbo) | ATENÇÃO | `fonte.regex_italico`, `fonte.excluir_area_carimbo` | `[APR-10] Texto em itálico fora do padrão.` | CEV “Porquê os seus títulos aparecem em itálico?” (11/2; em `7610-0005` são 458 trechos itálicos contra 31 do carimbo) | 1 |

### G. Consistência de vocabulário — `VOC`

| Código | Regra | Sev. | Parâmetro | Comentário na caixa vermelha | Fonte | Lote |
|---|---|---|---|---|---|---|
| VOC-01 | Mais de um termo do mesmo grupo de sinônimos no documento (ex.: TERRENO × TERRAPLENAGEM nos níveis) | ATENÇÃO | `grupos_sinonimos` (lista editável) | `[VOC-01] Termos diferentes para o mesmo elemento: {termos} — adotar um único padrão.` | CEV “Tem desenho saindo com "TERRENO" e desenho saindo com "TERRAPLENAGEM". Adotar um único padrão” (3/1), “EL.0,00 TERRENO” (6/1), “Adotar mesmo nome nos desenhos” (1/1), “trocar para "DET.05" assim mantemos a mesma nomenclatura” (2/1) | 1 |
| VOC-02 | Mesma palavra com e sem acento no documento (TÉRREO × TERREO, EMISSÃO × EMISSAO) | ATENÇÃO | `acentuacao.palavras_minimas_len` | `[VOC-02] Grafia divergente: "{forma_errada}" × "{forma_correta}".` | CEV “Ajustar ortografia - "TÉRREO"” (1/1), “Ajustar ortografia - "EMISSÃO"” (1/1) | 1 |
| VOC-03 | Mesmo nível (mesma elevação) com nomes diferentes entre vistas | ATENÇÃO | `niveis.regex` | `[VOC-03] Nível EL. {valor} nomeado como {nomes} em vistas diferentes.` | CEV “nivel terraplenagem em todo o desenho aparece” (13/1) | 2 |

### H. Relatórios — `REL`

Família para documentos **de texto** (memoriais descritivos, especificações, relatórios, planos — em geral A4, classes MD/ET/RL/PL/MF), em vez de pranchas. Verifica ortografia, numeração de itens, remissões internas e chamadas de figuras e tabelas.
**Sem evidência nos CEVs (§1.2-12). Proposta: adiar até termos relatórios verificados como referência.**

| Código | Regra | Sev. | Parâmetro | Comentário na caixa vermelha | Fonte | Lote |
|---|---|---|---|---|---|---|
| REL-01 | Palavra fora do dicionário pt-BR (Hunspell local) e fora do glossário técnico | ATENÇÃO | `ortografia.*` | `[REL-01] Verificar grafia: "{palavra}".` | briefing · CEV “corrigir ortografia” (1/1, em prancha) | 3 |
| REL-02 | Itemização quebrada (1.1 → 1.3; 2 → 2.1.1) | ERRO | `itemizacao.regex` | `[REL-02] Numeração de itens quebrada: {anterior} → {atual}.` | briefing | 3 |
| REL-03 | Remissão a item inexistente (“ver item 5.4”) | ERRO | `remissao.regex` | `[REL-03] Item {item} citado não existe no documento.` | briefing | 3 |
| REL-04 | Figura/Tabela sem chamada no texto | ATENÇÃO | `legendas.regex` | `[REL-04] {tipo} {n} sem chamada no texto.` | briefing | 3 |
| REL-05 | Numeração de item, figura ou tabela duplicada | ERRO | — | `[REL-05] Numeração duplicada: {numero}.` | briefing | 3 |

---

## 4. Deixados de fora de propósito (alto volume nos CEVs, mas não automatizáveis com segurança)

| Tema | Ocorrências nos CEVs | Por que fica fora |
|---|---|---|
| “Falta TAG aqui” (CP41, TQ02, RE30, TE30, TAG da janela?, TAG calha?) | ~ 90 | Exige saber qual elemento está desenhado naquele ponto |
| Conflito gráfico texto × traço / cota sobre parede | ~ 25 | O PDF vetorial não diz o que é cada traço; ruído alto |
| “Alinhar título ao desenho” / “aproximar do desenho” | ~ 20 | Exige delimitar a vista, o que é heurística frágil (pode virar lote 3) |
| Cotas faltando (PD, peitoril, calçada, eixo) | ~ 40 | Juízo técnico do que precisa ser cotado |
| Representação (shaded, halftone, hatch, profundidade de vista, ortofoto) | ~ 30 | Juízo gráfico |
| Decisões de projeto (corta-fogo, porta de aço, calha, NBR 9050, módulo de bloco) | ~ 150 | Juízo de engenharia: fora do escopo por definição |

---

## 5. Decisões

### 5.1 Registradas (23/10/2026)

| # | Decisão | Efeito |
|---|---|---|
| Q1 | Trecho marcado por **nuvem de revisão vermelha** ou apenas pela **ponta de seta da caixa de texto** | `anotacao.marcacao_trecho.modo = "nuvem"` quando o achado tem região (tabela, grupo de textos, campo do carimbo); `"so_seta"` quando é pontual. Sem Highlight e sem Linha translúcida. A `/Line` “Seta” separada fica desativada |
| Q1 (revista) | A ponta de seta da caixa não aparece no PDF-XChange. Pedido: faixa vermelha translúcida sobre o texto errado ou retângulo vermelho translúcido em volta do item | Cada achado agora grava três anotações vermelhas: **marcação** (faixa translúcida `/Line` “Linha”, opacidade 0,4, espessura igual à altura do texto, quando o alvo é um texto; retângulo translúcido `/Square` “Retângulo”, opacidade 0,25, quando o alvo é uma área — tabela ou campo do carimbo), **seta** separada (`/Line` “Seta”, `/IT /LineArrow`, W 2, ponta aberta no alvo) e a **caixa de texto**. A caixa é colocada num espaço livre da folha, sem cobrir textos do desenho. A nuvem continua disponível em `regras.json` |
| Q2 | Alturas nominais 1,5 e 2,0 mm; no máximo 4,0 mm no carimbo | APR-01 reescrita; ver Q2-b |
| Q3 | FL = Folha | `FL` excluído dos keynotes; nova PRA-11 |
| Q4 | Pedido de explicação | Família H explicada na §3-H; continua adiada |
| Q5 | TAG `CV-AQ-nnn` no início do comentário | Ver §2; código da regra só no CSV e no `/NM` |
| Q6 | Incluir valores quebrados, a validar pelo verificador final | TAG-07 confirmada como ATENÇÃO |
| Q7 | Pedido de explicação | Ver Q7 abaixo |
| Q8 | De acordo, como teste de funcionamento | Implementar o lote 1 só como teste, sem distribuir, e comparar com os CEVs |

| Q2-b | De acordo com a regra recomendada | APR-01 vale só para notas, tags, keynotes, cotas e corpo de tabela. Títulos de vista e de bloco, bolhas de eixo, nome de ambiente e título de tabela são classes do template, ficam fora da APR-01 e são cobertos pela APR-02 (desvio dentro da classe) |
| Q4 | Manter adiada | Família H fora do lote 1 |
| Q7 | De acordo com a dedução automática; a interface deve explicar cada campo | A ficha é aberta numa **janela simples (Tkinter, local, sem rede)** com **dica ao passar o mouse sobre o nome de cada campo**. Pela linha de comando, `--ajuda-ficha` mostra as mesmas explicações |

### 5.2 Histórico das perguntas (respondidas em 23/10/2026)

- **Q2-b — Textos do template fora de 1,5 / 2,0 mm.** Pela medição dos 40 CEVs, estes textos aparecem em **praticamente todas as folhas** fora do carimbo:

  | Corpo no PDF | Altura ≈ | Onde aparece | Situação |
  |---|---|---|---|
  | 5,0 pt | 1,3 mm | notas gerais (modelo 6110/7610) | abaixo de 1,5 |
  | 6,0 pt | 1,5 mm | tags, keynotes, tabelas, notas (Promon) | ✅ |
  | 8,0 pt | 2,0 mm | `A=`, `PD=`, textos de anotação | ✅ |
  | 8,6 pt | 2,1 mm | cotas, nomes de nível | ✅ (dentro da tolerância de 0,2) |
  | 10,0 pt | 2,5 mm | nome do ambiente na TAG, título de tabela | fora |
  | 16,0 pt | 4,0 mm | títulos de bloco (PLANTA-CHAVE, NOTAS GERAIS), marcas de corte | fora |
  | 17,2 pt | 4,3 mm | títulos de vista | fora |
  | 19,3 pt | 4,8 mm | bolhas de eixo | fora |

  Se a regra valer para tudo, ela comenta todas as folhas por causa do template, não do elaborador. Minha recomendação: aplicar APR-01 só a **notas, tags, keynotes, cotas e corpo de tabelas**; tratar títulos de vista, títulos de bloco, bolhas de eixo e nomes de ambiente como classes próprias, com altura fixa do template (e APR-02 pegaria quem sair dela). Os 2,5 mm do nome do ambiente e os 4,3 mm do título de vista estão errados, ou são padrão do template?
- **Q7 — Os dois campos extras da ficha:**
  - `esquema_revisao`: diz se a operação usa revisões **alfabéticas** (0, A, B, C…, padrão do PEG0007 9.4.4) ou **numéricas** (0, 1, 2…, permitido quando consta do procedimento da operação). Sem ele, a ferramenta não sabe se “depois da rev. 1 vem a 2” ou se “1” já está errado. Nas referências há os dois casos: `…-0503-…_R2` é numérico e `6110-…-P_A` é alfabético.
  - `classe_documento`: o tipo do documento (desenho `DE`/`DES`, memorial `MF`/`MD`, plano `PL`, especificação `ET`…). Ele decide quais famílias rodam: A–G para pranchas, H para relatórios.

  **Proposta para simplificar:** a ferramenta **deduz os dois sozinha**. A classe vem do número do documento (`3-N-T012-0503-B-ARQ-**DE**-0001`, `6110-AQT-**DES**-0010`). O esquema de revisão vem da revisão atual (letra = alfabético, número ≥ 1 = numérico). O formulário só pergunta quando não há como deduzir (rev. 0 numa operação nova). Os valores ficam gravados na `.ficha.json` e você pode corrigi-los.
- **Q4 — Família H:** com a explicação da §3-H, manter adiada ou retirar do escopo?

---

## 6. Teste de funcionamento do lote 1 (23/10/2026)

**Como foi feito:** `ferramentas/validar_referencias.py` roda o verificador nos 40 CEVs, sem ficha, e para cada achado procura uma marca vermelha sua num raio de 15 mm. Ele considera as anotações e também os comentários de rodadas anteriores que ficaram achatados no conteúdo. O detalhe por achado está em `saida_teste/validacao.csv` e os PDFs anotados em `saida_teste/*_CEV_auto.pdf`; a pasta está no `.gitignore`.

**Volume final:** 94 achados em 33 dos 40 documentos (57 ERRO, 37 ATENÇÃO), cerca de 2,4 por documento. A primeira rodada teve 311 achados. O ruído caiu com as correções da leitura de tabelas e com as mudanças de regra abaixo.

### 6.1 Achados que coincidem com o seu próprio comentário

| Regra | Caso | Seu comentário no local |
|---|---|---|
| APR-06 | Perspectiva sem escala, 7 de 9 casos | “SEM ESCALA” |
| PRA-06 | `6110-0010`: folhas “01/02” num PDF de 4 folhas | “01/04 DEVE CORRESPONDER AO TOTAL DO PROJETO” |
| PRA-06 / PRA-10 / CAR-03 | `7610-0005`: “7210-AQT-DES-XXXX”, folha 1/1 com 2 folhas | “vamos aguardar a numeração” |
| PRA-09 | `6110-0001`: itens 06 e 07 com o mesmo código | “…itens 06 e 07 com o mesmo código” |
| KEY-01 | `1302-0004`: RE21 sem linha na tabela | “Não há o RE21 nas tabelas de quantidades” |
| KEY-01 | `1311-0001`: TE20 sem linha na tabela | “TE30?” |
| TAB-02 | `0503-0001_R2`: Tabela de Forros vazia | “foram apagados os revestimentos de teto??” |
| TAB-03 | `1304-0001`: Quadro de Áreas sem construída/coberta | “Rever quadro de áreas, colocar ÁREA CONSTRUIDA / ÁREA COBERTA” |
| TAB-04 | “m²” repetido nas células: 25 casos em 14 docs, vários com o seu comentário no mesmo ponto | “Suprimir "m²" após o valor…” |
| CAR-07 | `0208-1001`: “EMISSÕA INICIAL” | “Ajustar ortografia - "EMISSÃO"” |
| CAR-03 | `1302-0004`: carimbo rev. 1 × arquivo R0 | “0” |
| PRA-10 | `1304-0001`: “E.RUMO012-AQX-XXXXX” | o número correto escrito por você |
| APR-10 | `7610-0005`: títulos e bolhas em itálico | “Porquê os seus títulos aparecem em itálico?” |

### 6.2 Achados reais que não estão comentados nos CEVs (para você conferir)

- **CAR-03:** em `1302-0011` o carimbo diz `…-ARQ-DE-0001` (o arquivo é `-0011`); em `6110-0014` o carimbo diz `6110-AQT-DES-0001-P`.
- **CAR-07:** em `7610-0002` o histórico tem “EMISSÃO INCIAL”.
- **PRA-06:** em `1303-0001` as três folhas estão como “01 / 03”; em `7610-0002` o total é 4 numas folhas e 5 noutras.
- **TAB-03:** em `6110-0011` o Quadro de Áreas tem duas linhas “ÁREA CONSTRUÍDA” e nenhuma “ÁREA COBERTA”.
- **CAR-01:** em `1302-0001_R2` e `3-N-T019-0200` o campo REV do carimbo está vazio. Confirme se o valor existe como desenho (não texto).
- **APR-05:** em `1303-0001` 10 linhas das notas passam da borda da folha.

### 6.3 Mudanças feitas por causa do teste

| Regra | Mudança | Motivo |
|---|---|---|
| APR-04 | Rebaixada para lote 3 | As duplicatas exatamente sobrepostas (ex.: “(ACAB.)” 2×) não aparecem na plotagem e você nunca comentou |
| VOC-02 | Rebaixada para lote 2 | Deu 34 achados (NIVEL, AREA, PAINEIS…) que você não comenta. Sem dicionário a regra não sabe qual forma é a correta (FERROVIA × FERROVÍA). Volta junto com o Hunspell (REL-01) |
| VOC-01 | Ativa, mas **0 achados** | O seu caso real compara **documentos diferentes**: `0208` usa TERRAPLENAGEM e `0503-1001` usa TERRENO. Dentro de cada documento não há divergência. Falta um modo “vários PDFs da mesma operação” |
| PRA-01 | Só em documento de edificação (tem TAG `A= … m²`) | Plano diretor, cercas e paisagismo não têm planta-chave/notas por natureza |
| TAB-01 | Cada tabela só é exigida quando o desenho usa o prefixo correspondente | Prefixo → tabela levantado dos 40 CEVs |
| APR-06 | Só nas folhas que usam “ESCALA 1 : N” sob o título | Evita comentar folhas de outro modelo (GRL, paisagismo) |
| APR-10 | Ignora nomes científicos em itálico (“Eugenia uniflora”) | No paisagismo, o itálico é a convenção correta |
| APR-05 | ATENÇÃO, com tolerância de 0,5 mm | A caixa do texto inclui o avanço do último caractere |
| CAR-03 | Também compara o **número** do carimbo com o nome do arquivo | Achou 3 documentos com número errado |
| Todas | O mesmo comentário repetido em várias folhas sai uma vez, com “(também nas folhas 2, 3)” | Carimbo e tabelas se repetem em cada folha |

### 6.4 O que o teste não cobriu

- **CAR-02 e PRA-05 (comparação com a ficha):** só testei com uma ficha sintética, em `0503-0001_R2`. A comparação funcionou, mas não há fichas reais das 40 emissões.
- **Formulário da ficha:** abre e fecha sem erro num teste automático, mas ninguém o usou de verdade.
- **Aparência no PDF-XChange:** as anotações foram verificadas renderizando com o PyMuPDF (caixa vermelha com seta, nuvem vermelha). Não abri os arquivos no PDF-XChange; a aparência lá precisa da sua conferência.
- **Executável PyInstaller:** ainda não foi gerado.

---

## 7. PROPOSTA — Família LD: conferência com a Lista de Documentos (aguarda aprovação)

### 7.1 O que as LDs de referência mostram

As duas LDs (`E.POTA001-PL2-00001`, `E.MRSA003-PL2-01001`) seguem o **modelo padrão Promon**:
- **Aba `LD - Promon`:** cabeçalho na 2ª linha. Colunas `No Promon` | `No Cliente` | `Título`, e na coluna A o código de ação: D = documento, A = atividade, M = modelagem, E = excluir.
- **Abas `LD - Cliente` e `Colaborativo`:** trazem a revisão e o estado de cada emissão. Ficam para uma fase posterior.

A leitura usa só a biblioteca padrão do Python, sem dependência nova. A LD E.POTA001 (17 MB, 2.210 documentos) é lida em cerca de 3 s.

### 7.2 Teste de viabilidade (script descartável, LD E.POTA001 contra `6110-0007` e quatro CEVs Autazes)

| Documento | Lista de referências no PDF | Na LD |
|---|---|---|
| `6110-0007`, `7610-0003` | **2210-ATQ-DES-0001-P** / **7210-ATQ-DES-0001-P** | não existe; seria **…-AQT-DES-0001-P** (letras trocadas) |
| `6110-0007`, `6110-0001` | 2010-AQT-CTP-0001-**P** | só existe 2010-AQT-CTP-0001-**B** |
| `6110-0010` | 2010-AQT-CTP-0001 (sem sufixo) | idem |
| `6110-0010` | …ARRANJO SIST. **SUBETRRÂNEOS** | ARRANJO DE SISTEMAS SUBTERRÂNEOS |
| `6110-0001` | 2010-IHD-DES-0005-P em dois itens | (a PRA-09 também acusa) |
| vários | INFRAESTRUTURA - GERAL - DRENAGEM DE PROTEÇÃO | INFRAESTRUTURA - PLANTA - GERAL - DRENAGEM DE PROTEÇÃO DE TERRAPLENAGEM |
| `7610-0003` | INFRA. E EQUIPAMENTOS · TUBULAÇÃO - LAYOUT GERAL… | INFRAESTRUTURA E EQUIPAMENTOS · LAYOUT GERAL… |
| carimbo `7610-0003` | ARQUITETURA - **INST.** E EQUIPAMENTOS… | ARQUITETURA - **INSTALAÇÕES** E EQUIPAMENTOS… |

Os títulos de carimbo seguem o padrão “nome do projeto + título da LD + vistas da folha”, por exemplo “PROJETO AUTAZES / ARQUITETURA - … - ALMOXARIFADO / PLANTAS, CORTES…”. Por isso a comparação verifica se o título da LD **está contido** no título do carimbo; não exige igualdade.

### 7.3 Regras propostas

| Código | Regra | Sev. | Comentário na caixa vermelha | Fonte |
|---|---|---|---|---|
| LD-00 | LD carregada é de outra operação que não a do documento; a conferência com a LD não é feita (pré-condição da família) | ATENÇÃO | `A LD carregada é da operação {op_ld}, mas o documento é da {op_doc} — conferência com a LD não realizada.` | L1 (só serve LD da mesma operação) |
| LD-01 | Código citado nos Documentos de Referência não existe na LD (nem como Nº Promon nem como Nº Cliente). Quando há código da LD muito parecido (diferença de até 2 caracteres ou letras trocadas), ele é sugerido | ERRO | `Documento {codigo} não consta na LD.` / `Documento {codigo} não consta na LD — seria {sugestao} ("{titulo_ld}")?` | sua sugestão · CEV “a lista de documentos de referência precisa estar com a nomenclatura conforme os títulos da Lista de Documentos” (2/2), “Esses documentos estão em conformidade com a LD da Fase 2?” (2/1) |
| LD-02 | Código existe, mas o título citado difere do título da LD. Diferenças só de espaço e pontuação são ignoradas; abreviações (INFRA., SIST., INST.) e palavras faltando ou trocadas são apontadas | ATENÇÃO | `Título difere da LD: "{titulo_ld}".` | idem · “O título deve estar igual à LD”  **desativada em 10/11/2026** (§21: vale só o número) |
| LD-03 | Documento citado está marcado como Excluir (E) na LD | ERRO | `Documento {codigo} está excluído da LD.` | PEG7 9.4.8 |
| LD-04 | Número do carimbo não existe na LD | ERRO | `Número do documento ({numero}) não consta na LD.` | PEG7 9.4.1 |
| LD-05 | Título da LD não está contido no título do carimbo | ATENÇÃO | `Título do carimbo difere da LD: "{titulo_ld}".` | PEG7 9.4.8 · “O título deve estar igual à LD” |
| LD-06 | Pré-preenche a ficha com número, título (da LD) e cliente/operação. Não comenta nada | — | — | sua sugestão (reduzir digitação) |

### 7.4 Decisões que preciso de você

- **L1 — Como a ferramenta acha a LD.** Minha recomendação é a opção (a) com (b) como reforço:
  - (a) campo **“LD do projeto”** na ficha, com botão para escolher o arquivo e caminho lembrado por operação (`E.POTA001`, `E.COAM001`…);
  - (b) busca automática de `*-PL2-*.xlsx` na pasta do PDF e nas pastas acima;
  - (c) opção `--ld` na linha de comando.
- **L2 — Rigor do título (LD-02).** Abreviar (“INFRA.”, “SIST.”) conta como divergência? Pelo seu comentário entendo que sim, como ATENÇÃO.
- **L3 — Nº Promon × Nº Cliente.** A lista do PDF pode citar qualquer um dos dois (Autazes cita o do cliente, RUMO cita o Promon). A ferramenta aceita ambos. Deve exigir o mesmo tipo que o carimbo usa?
- **L4 — LDs dos projetos de teste.** COAM001 e GPEN006 não têm LD na pasta. Pode incluir para eu testar também nesses modelos?

---

## 8. PROPOSTA — Família CON: informação faltante (aguarda aprovação)

### 8.1 O que já existe

| Item pedido | Regra atual | Situação |
|---|---|---|
| Descrição de TAG faltando (código no desenho sem linha na tabela) | KEY-01 | ativa; acertou RE21 e TE20 nos CEVs |
| Tabela sem linhas | TAB-02 | ativa |
| Vista sem escala | APR-06 | ativa |
| TAG de ambiente sem PD, área ou acabamentos | TAG-01 / TAG-02 | escritas, mas não implementadas (lote 2) |

### 8.2 Teste nos 40 CEVs (scripts descartáveis)

O teste recortou cada folha em vistas (título + área acima dele) e contou o que existe em cada uma:

| Vista | Nº | Com cota de nível (EL.) | Com inclinação (%) | Com descida AP (DESCIDA / TQnn) | Com cotas numéricas |
|---|---|---|---|---|---|
| Planta baixa | 55* | 37 | — | — | 40 |
| Planta de cobertura | 30 | — | **29** | **7** | 30 |
| Corte | 92 | **92** | — | — | 92 |
| Elevação | 154 | **153** | — | — | 150 |

\* inclui “PLANTA GERAL” de implantação e de paisagismo, que não têm cotas de edificação; seriam excluídas.

**Leitura dos números:**
- O teste “a vista tem alguma cota ou nível?” quase nunca dispara. É uma rede de segurança barata, mas pega pouca coisa.
- **Os seus comentários são sobre um item específico faltando:** “PD?” (12×), “Cota da Calçada?”, “COTA P.D.”, “Faltou cotar o PD e o entreforro”, “cotas de amarração do portão?”. Isso exige saber o que está desenhado em cada ponto. Com o texto do PDF não dá para fazer com segurança.
- **Descida de água pluvial:** falta em 23 das 30 coberturas. Em 6 delas você comentou exatamente isso (“NÃO ENCONTREI INDICAÇÃO DAS DESCIDAS DE ÁGUA PLUVIAL” 8×, “DESCIDA AP?”, “INDICAR CALHA E TUBO DE QUEDA”). Nas outras 17, provavelmente a descida está só como símbolo. Como ERRO seria barulhento; como ATENÇÃO é uma pergunta útil.
- **TAG de ambiente sem PD:** 26 de 265 TAGs. Coincide com o seu “PD = ??” em `1302-0004` (2 casos); os demais precisam de ajuste do agrupamento.
- **Linha de tabela com célula vazia** (descrição, quantidade, dimensão): o teste deu 90 casos, quase todos falsos, porque a leitura de colunas pelo texto não é precisa. Para funcionar, ela precisa usar as linhas de borda das tabelas, que são vetores no PDF. É viável, mas dá mais trabalho.

### 8.3 Regras propostas

| Código | Regra | Sev. | Comentário | Evidência | Lote |
|---|---|---|---|---|---|
| CON-01 | Planta baixa, corte ou elevação **sem nenhuma** cota de nível | ATENÇÃO | `Vista sem cota de nível — indicar EL. dos pisos/níveis.` | CK B30, B61, B72 · dispara em 1 de 246 vistas | 1 |
| CON-02 | Planta de cobertura sem inclinação (`%` / `i=`) | ATENÇÃO | `Indicar a inclinação (caimento) de cada água da cobertura.` | CK B50 · 1 de 30 | 1 |
| CON-03 | Planta de cobertura sem descida de água pluvial (texto DESCIDA / A.P. / código TQ) | ATENÇÃO | `Não encontrei indicação das descidas de água pluvial.` | CK B54 · seu comentário 8× + 3 variantes · dispara em 23 de 30 | 2 |
| CON-04 | Cota entre eixos ausente: para cada par de eixos vizinhos (bolhas da malha), procurar a cota entre eles e a cota total | ATENÇÃO | `Falta cota entre os eixos {e1} e {e2}.` | CK B32, B69 · “Atentar-se à ordem das cotas 1) geral dos eixos 2) entre eixos…” (4×), “cade o restante da indicação do eixo??” | 2 (prototipar) |
| TAG-01 | TAG de ambiente sem PD (ou sem área) | ERRO | `TAG do ambiente {ambiente}: falta {item}.` | “PD?” (12×), “PD = ??” · 26 de 265 TAGs | 2 → implementar e calibrar |
| TAG-02 | TAG de ambiente com menos de 3 acabamentos | ATENÇÃO | (já no catálogo) | 22 de 265 TAGs | 2 → idem |
| TAB-06 | Linha de tabela com TAG, mas sem descrição, dimensão ou quantidade | ERRO | `{codigo}: preencher {coluna} na {tabela}.` | exige ler as bordas das tabelas | 3 (depende de leitura por grade) |

### 8.4 Fora de alcance (continua com você)

Cota específica faltando num ponto do desenho (PD de um ambiente no corte, calçada, amarração, balanço), TAG faltando num elemento (janela, calha, pingadeira) e leitura do que a geometria representa. O PDF só diz que há traços, não o que eles são.

### 8.5 Implementação e teste (23/10/2026)

| Regra | Estado | Nos 40 CEVs |
|---|---|---|
| CON-01 | ativa, ATENÇÃO | 0 achados: todas as plantas, cortes e elevações de edificação têm EL. Funciona como rede de segurança |
| CON-02 | ativa, ATENÇÃO | 1 achado (`7610-0003`, folha 5) |
| TAG-01 | ativa, ERRO | 26 achados em 7 docs, 22 junto de comentário seu. Bate com os seus “PD?” em `6110-0011` (7 ambientes) e “PD = ??” em `1302-0004` |
| TAG-02 | ativa, ATENÇÃO | 22 achados em 9 docs. Bate com “TAG do ambiente com os acabamentos” e “TE30?”. Em `7610-0002/0003` aparecem áreas abertas (circulação, pátio coberto) que você não comentou |
| CON-03 | protótipo, inativa (lote 2) | 22 achados em 20 docs, 5 batem com “não encontrei descidas…”. Barulhenta: a descida costuma ser só um símbolo |
| CON-04 | protótipo, inativa (lote 2) | 8 achados em 3 docs, sem confirmação nos seus comentários. Precisa de amostra maior |

Para rodar os protótipos: `python -X utf8 -m verificador --lote 2 arquivo.pdf`.

## 9. Anotação de todas as ocorrências (23/10/2026)

**Pedido:** quando a mesma falha aparece várias vezes, cada ocorrência deve ser anotada.

**Como ficou:** a falha recebe **uma caixa por folha**, com faixa ou retângulo vermelho em **cada** ocorrência e uma seta da caixa até cada uma. O limite é de 12 setas por caixa (`anotacao.max_setas_por_achado`); acima disso as demais ocorrências ficam só com a faixa. O texto termina com “(N ocorrências nesta folha)”, e o CSV ganhou a coluna `ocorrencias`.

**Regras que passaram a marcar todas as ocorrências:** KEY-01/02 (código usado várias vezes), APR-05 (todos os textos cortados), APR-10 (todo o itálico), TAG-05, VOC-01, PRA-08 (todas as citações do mesmo item) e PRA-10 (o mesmo texto provisório repetido).

**Entre folhas:** cada folha recebe a sua caixa, inclusive para carimbo e tabelas repetidos (`anotacao.agrupar_entre_folhas = false`). Antes saía uma caixa só, com “(também nas folhas …)”.

### 7.5 Implementação e teste da família LD (23/10/2026)

**Decisões aplicadas:**
- **L1:** a LD é encontrada nesta ordem: campo “LD do projeto” na ficha (com botão para escolher o arquivo) → última LD usada na operação (gravada em `%APPDATA%\VerificadorCEV\lds.json`) → busca de `*-PL2-*.xlsx` na pasta do PDF e até 4 pastas acima. **Só serve a LD da mesma operação** (E.POTA001, E.COAM001…). Também dá para indicar o arquivo com `--ld` ou desligar a busca com `--sem-ld`.
- **L2:** abreviação conta como divergência (ATENÇÃO). O comentário mostra a diferença palavra a palavra, por exemplo `NFRAESTRUTURA → INFRAESTRUTURA` ou `falta: DE TERRAPLENAGEM`.
- **L3:** a lista pode citar tanto o Nº Promon quanto o Nº Cliente.

**Pré-preenchimento da ficha (LD-06):** o número sai do nome do arquivo e o título sai da LD.

**Resultado nos 14 CEVs Autazes e no `6110-0007`, com a LD E.POTA001:**
- **LD-01, códigos com erro de digitação, com sugestão do código certo:** 2210-**ATQ**, 2010-**IIHD**, 2010-**IDH**, **201O**-TUB (letra O no lugar do zero), CTP-0001-**P** e CTP-0001 sem sufixo.
- **LD-02, títulos:** NFRAESTRUTURA, SUBETRRÂNEOS, SISTT, abreviações (SIST., INFRA.), palavras faltando e o prefixo “TUBULAÇÃO -” que não existe na LD.
- **LD-04:** número do carimbo `7210-AQT-DES-XXXX`.
- **LD-05:** título do carimbo com “INST.” e diferenças em `7610-0002/0003`.

**Volume:** como a lista de referências se repete em cada folha e cada folha recebe a própria caixa, o LD-02 gerou 117 caixas em 11 documentos. Se ficar pesado na prática, dá para agrupar a lista por documento.


## 10. Interface (23/10/2026)

**Janela** (`verificador/interface.py`, Tkinter, local):
- **Fluxo:** 1 · Arquivos → 2 · Opções (LD, pasta de saída, ficha) → Verificar → 3 · Resultado.
- **Resultado:** números por severidade, filtro Todos/Erro/Atenção, tabela de achados, comentário completo do achado selecionado e botões para abrir o PDF anotado, o relatório e a pasta.
- **Processamento:** roda em segundo plano; a ficha de cada PDF abre como janela modal no mesmo tema.

**Identidade** (`verificador/tema.py`), conforme `promon-parametros-formatacao.md`:
- **Cores:** fundo `#EDF1F4`; cabeçalho branco com título 18 px em azul e filete laranja de 2 px; botão principal azul. O laranja aparece só como acento.
- **Fonte:** Soleto → Arial → Tahoma. Nesta máquina a Soleto não está instalada, então a janela usa Arial.
- **Severidade:** ERRO e ATENÇÃO sempre escritos, com a cor de estado.

**Modo escuro:**
- **Janela:** lê `AppsUseLightTheme` no registro do usuário (só leitura) e aplica os tokens escuros do MD §2.1. Verifica a cada 3 s, então acompanha a troca de tema do Windows com a janela aberta. A barra de título do Windows segue o tema.
- **Relatório HTML:** usa `prefers-color-scheme`.

**Relatório HTML** (`…_CEV.html`): autocontido, sem nenhum recurso da internet. Traz números por severidade, filtro, tabela com "procede / não procede" e observação por achado, e exportação da avaliação em CSV para o piloto.

**Seta duplicada (correção):** a 1ª ocorrência usa só a seta da própria caixa de texto; a seta separada é desenhada apenas para as ocorrências adicionais.


## 11. Interface em HTML — caminho A (23/10/2026)

**Montagem:**
- **Janela:** `verificador/interface_web.py` + `verificador/web/index.html`. Usa pywebview 6.2.1 sobre o WebView2 do Windows (versão 155 nesta máquina).
- **Página:** local e autocontida, sem nada da internet.
- **Ponte:** a classe `Api` liga a página ao Python. Os diálogos de arquivo são os do Windows e devolvem o caminho real.

**Funções:**
- **Arquivos:** arrastar PDFs direto para a janela (o WebView2 entrega o caminho completo do arquivo) ou "Adicionar PDFs…".
- **Ficha:** diálogo modal dentro da própria página, com explicação ao passar o mouse sobre o ⓘ e botão para escolher a LD.
- **Resultado:** números por severidade, filtro, tabela com "procede / não procede", comentário completo do achado selecionado com observação, e botões para abrir o PDF anotado, o relatório e a pasta.
- **Avaliação:** "Salvar avaliação" grava `avaliacao_AAAAMMDD_HHMM.csv` ao lado dos arquivos anotados.

**Modo claro/escuro:** segue o Windows pelo `prefers-color-scheme`, que o WebView2 acompanha. A barra de título acompanha também.

**Reserva:** se o pywebview ou o WebView2 faltarem, abre a janela Tkinter (seção 10).

**Teste:** a janela real verificou os 3 PDFs de `referencias/originais` de ponta a ponta. As imagens da página nos dois temas foram geradas com o Edge sem interface, porque a tela estava bloqueada durante o teste.

**Memória da LD:** com o Python da Microsoft Store, `lds.json` fica em `%LOCALAPPDATA%\Packages\PythonSoftwareFoundation…\LocalCache\Roaming\VerificadorCEV`. Hoje ele aponta a LD do SharePoint do projeto E.POTA001.


## 12. Saídas opcionais (25/10/2026)

**Pedido:** o CSV não é necessário sempre. O operador escolhe se quer as saídas em CSV e em HTML.

**O que ficou:**
- O `_CEV.pdf` é sempre gravado.
- Em "Arquivos gravados" (janela HTML e janela reserva) há **Relatório HTML** (padrão: ligado) e **Lista em CSV** (padrão: desligado).
- **Na janela HTML a escolha do operador fica lembrada** em `VerificadorCEV\preferencias.json`, junto com a opção de preencher a ficha.
- Os padrões ficam em `regras.json → saidas`. Na linha de comando: `--csv`, `--sem-csv`, `--html`, `--sem-html`.
- Se o relatório não foi gravado, o botão "Abrir relatório" avisa em vez de falhar.
- A avaliação do piloto ("Salvar avaliação") continua sendo um CSV à parte, gravado só quando o operador pede.


## 13. Padrão visual Promon e logo (25/10/2026)

**Pedido:** a interface deve seguir o padrão Promon. Faltava o logo da Promon ao lado do nome da ferramenta.

**O que ficou (conforme `promon-parametros-formatacao.md`):**
- **Logo oficial** com 30 px de altura e área de proteção (x/2) livre ao redor. Fica à esquerda do título, separado dele por uma régua vertical (§7.1).
  - A versão **positiva** aparece no modo claro e a **negativa** no escuro (§5).
  - Os arquivos vêm da pasta *Logos Promon Engenharia* dos padrões internos. Só a margem transparente foi recortada.
  - Ficam em `verificador/web/img/`.
- O logo aparece em três lugares:
  - na janela HTML;
  - no relatório `_CEV.html`, embutido no próprio arquivo, que continua sem dependências;
  - na janela reserva Tkinter, que troca de versão junto com o tema.
- **Fonte:** Soleto, depois Mulish, Tahoma e Arial. A Soleto não está instalada neste computador, então os testes usaram Tahoma. Embutir a Mulish é uma opção para o futuro.
- **Sombra:** uma única sombra suave, também nos diálogos (§0).
- **Textos de estado:** peso 800 (§1.6).
- **Cartões de números:** ganharam sublegenda (§7.1).
- **Teste:** capturas dos dois temas da janela e do relatório geradas com o Edge sem interface. O logo da janela Tkinter carrega e é reduzido para 30 px.


## 14. Executável para distribuição (26/10/2026)

**Pedido:** permitir que outras pessoas rodem a ferramenta sem instalar Python.

**O que ficou:**
- `ferramentas\gerar_exe.bat` gera `dist\VerificadorCEV\` com o exe, o `Verificador.bat`, o `regras.json` e o `LEIA-ME.txt`. O exe tem cerca de 40 MB e é gerado com PyInstaller `--onefile --windowed`.
- O ponto de entrada é `ferramentas\entrada_exe.py`.
- **30/10/2026:** o pacote ganhou o `verificador-cmd.exe` (mesmo ponto de entrada, `--console`) para rodar pelo cmd com mensagens e código de saída. Testado fora do projeto: CSV idêntico ao da versão Python, saída 0 com sucesso e 1 com PDF inexistente.

**Teste, com o exe sozinho numa pasta fora do projeto e sem `regras.json` ao lado:**
- os 3 PDFs de `referencias/originais` geraram CSVs idênticos aos da versão Python;
- a janela HTML abriu pelo `Verificador.bat` com o PDF arrastado já na lista.


## 15. Versão Claude — revisão assistida (28/10/2026)

**Pedido:** ter duas versões sempre alinhadas, a offline e a Claude.
- A versão Claude incorpora o que está fora de escopo na offline, inclusive questões técnicas, como no exemplo de Instrumentação.
- Usa o **critério de projeto** da operação (metodologia construtiva e parâmetros) como base de comparação.
- O uso de documentos com o Claude está coberto pela licença enterprise, conforme a usuária.

**Como ficou:**
- **Skill `revisao-assistida-arquitetura`:**
  1. `ferramentas/preparar_revisao.py` roda as regras offline e grava imagens das folhas (visão geral + 6 recortes ampliados), texto com posição em mm, carimbo e texto do critério de projeto;
  2. o Claude revisa e escreve `<nome>.revisao.json`;
  3. `python -m verificador --revisao …` grava o mesmo `_CEV.pdf`, relatório e CSV.
- **Critérios RA** em `regras.json → revisao_assistida.criterios`:

  | Código | Critério |
  |---|---|
  | RA-01 | TAG faltando |
  | RA-02 | Cota ou nível faltando |
  | RA-03 | Conflito gráfico |
  | RA-04 | Organização da folha |
  | RA-05 | Representação |
  | RA-06 | Coerência entre vistas |
  | RA-07 | Notas × desenho |
  | RA-08 | Critério de projeto |
  | RA-09 | Normas |
  | RA-10 | Solução de projeto |
  | RA-11 | Escala |
  | RA-12 | CheckList AQ |

  Cada tema da §4 tem um RA correspondente.
- **Severidades:** ERRO (Corrigir), ATENÇÃO, CORRETO.
  - CORRETO não vai para o PDF, que continua só vermelho; aparece no relatório (cartão e filtro próprios) e no CSV.
  - O relatório e o CSV indicam a origem de cada achado (Verificador × Revisão assistida).
- **Alinhamento:**
  - um único `regras.json` e um único anotador e relatório;
  - a versão Claude sempre inclui as regras offline;
  - um achado mecânico do Claude vira proposta de regra offline;
  - `ferramentas/checar_alinhamento.py` confere regras × catálogo × skills × fora de escopo.

**Teste numa folha original com 2 folhas:**
- **Offline:** 4 achados, inalterado.
- **Versão Claude:** mais 7 achados, sendo 1 ERRO, 4 ATENÇÃO e 2 CORRETO.
- **Lacuna da offline encontrada:** a TAG de piso PI11 é usada na planta, mas não existe na Tabela de Revestimento de Piso, e a KEY-01 não detectou. Fica como pendência offline: investigar por que a KEY-01 não pegou.
- **PDF:** 9 caixas vermelhas; o original ficou intacto.


## 16. Correção: famílias puladas nos documentos E.* (28/10/2026)

**Sintoma:** a revisão assistida achou o PI11 usado na planta e ausente da Tabela de Revestimento de Piso, e a KEY-01 não detectou.

**Causa:**
- A classe do documento (DE/DES) era deduzida só dos números `…-ARQ-DE-…` e `…-AQT-DES-…`.
- Na numeração Promon `E.GPEN006-AQ4-20004` a classe ficava vazia, e as famílias que só rodam em prancha eram puladas **sem aviso**: KEY, TAB-01, PRA-01, CON, TAG-01/02, APR-10 e CAR-00.
- Os 40 CEVs de referência não têm nenhum número E.*, por isso a validação não expôs o problema.

**Correção:**
- `ficha.deducao_automatica.classe_por_assunto` deduz a classe pelo assunto do PEG0007: AQ1 → CP, AQ2 a AQ5 → DE, AQ8 → ET. AQ6, AQ7 e AQ9 continuam sem classe.
- A versão Claude passou a procurar o critério de projeto também pelo assunto AQ1.

**Falsos positivos que apareceram no modelo de folha E.* e foram corrigidos:**
- **CON-01:** "EL. +0,34" não era reconhecido, porque a expressão aceitava só o sinal de menos. Eram 5 falsos positivos numa folha.
- **PRA-01:** a planta-chave desse modelo se chama "Planta de Situação / Plant Situation", que agora é variante aceita.

**Resultado:**
- Nos 40 CEVs, nada muda (184 achados antes e depois).
- Nos originais E.*:
  - GPEN foi de 4 para 12 achados: KEY-01 PI11, 4 TAG-01 sem PD, 1 CON-01 real (Corte 2 sem EL) e 2 TAB-01;
  - COAM foi de 5 para 33, sendo 17 TAG-01 e 7 TAG-02, porque nenhuma TAG do documento tem PD.

**Pendências, a decidir com a usuária:**
- ~~agrupar a TAG-01/02 por folha~~: feito (§17);
- exigência do Quadro de Ambientes/Áreas em folhas de ampliação;
- CON-01 em planta de demolição e em corte perspectivado.


## 17. TAG-01/02 agrupadas por folha (28/10/2026)

**Pedido:** agrupar a TAG-01/02. Quando o modelo de TAG não traz PD, saía um comentário por ambiente, 17 numa só folha.

**Como ficou:**
- Um comentário por folha, listando até 6 ambientes (`max_ambientes_listados`) e "e mais N".
- Cada TAG continua marcada no PDF, com faixa e seta, e o texto termina com "(N ocorrências nesta folha)".
- Com um só ambiente na folha, sai o texto individual de antes.
- Os textos ficam em `comentario_agrupado`, no `regras.json`.

**Resultado:**

| Onde | Antes | Depois |
|---|---|---|
| 40 CEVs, TAG-01 | 26 caixas | 7 caixas, as mesmas 26 TAGs marcadas |
| 40 CEVs, TAG-02 | 22 caixas | 11 caixas, as mesmas 22 TAGs marcadas |
| 40 CEVs, total | 184 achados | 154 achados |
| COAM | 33 achados | 13 achados |
| GPEN | 12 achados | 10 achados |
| 6110 | 6 achados | 5 achados |


## 18. Quadros só nas plantas gerais e planta-chave de setorização (28/10/2026)

**Decisão da usuária:** Quadro de Ambientes e Quadro de Áreas só são exigidos nas plantas gerais.
- A TAB-01 passou a exigir os dois quadros só quando o documento tem vista PLANTA BAIXA ou PLANTA (`exigir_se.tipos_vista`).
- Nas ampliações (GPEN), a cobrança deixou de aparecer.
- Nos 40 CEVs, nada muda (4 → 4).

**Pedido:** verificar se as plantas gerais têm planta-chave de layout/departamentos, e propor um padrão para as legendas.

**Diagnóstico de 7 plantas-chave de projetos diferentes:**
- o mesmo setor aparece com cores diferentes: APOIO em 3 cores, UTILIDADES em 3 cores;
- setores diferentes aparecem com a mesma cor: REUNIÕES, LIMPEZA e ESTOCAGEM em verde-claro;
- algumas legendas listam nomes de ambiente (S. FEM., COPA) com abreviação, em vez de setores;
- a legenda não tem modelo: de 1 a 3 colunas, tamanhos variados, sem título;
- há textura sobre a cor.

**Proposta do padrão** (`padroes/padrao-setorizacao.html`, `regras.json → setorizacao`):
- **Cores:** 13 setores fixos e 4 cores complementares, em tons claros calculados a partir das cores Promon. A menor diferença entre setores é ΔE 11,9, o contraste do texto é de pelo menos 6:1, e não há cor saturada das marcas de verificação.
- **Legenda:** título SETORIZAÇÃO, amostra de 6 × 4 mm, texto de 2,0 mm, até 2 colunas, ordem fixa, nomes completos, cor lisa e área opcional.
- **Implantação:** parâmetro `PRM_Setor` e esquema de cores `PRM-SETORIZACAO` no template Revit.

**Verificação:**

| Código | Regra | Sev. | Situação |
|---|---|---|---|
| PRA-12 | Documento com planta geral sem planta-chave de setorização | ATENÇÃO | proposta, lote 2 |
| PRA-13 | Cor do setor fora da paleta (tolerância ΔE 3) | ERRO | proposta, lote 2 |
| PRA-14 | Legenda × planta: cor preenchida sem item na legenda, ou item sem uso na planta | ERRO | proposta, lote 2 |
| PRA-15 | Nome fora da lista padrão de setores | ATENÇÃO | proposta, lote 2 |
| RA-13 | Versão Claude: planta-chave de setorização e aderência ao padrão | — | ativo |

- **PRA-12 a PRA-15:** devem ler as cores dos preenchimentos vetoriais do PDF e as amostras da legenda. Aguardam PDFs com planta-chave para validar; as imagens recebidas não têm os vetores.
- **RA-13:** já funciona por imagem.


## 19. Setorização: implementação e teste (30/10/2026)

**Material:** 5 PDFs emitidos com planta-chave de setorização (6110-0001, 0002, 0014, 7610-0002 e 5420-0001) e os 40 CEVs.

**Como é lida:**
- A legenda vem dos vetores do PDF: são 3 ou mais amostras preenchidas do mesmo tamanho (4 a 9,5 mm), cada uma com um nome à direita.
- A legenda só conta como **de setorização** quando metade ou mais dos nomes são setores conhecidos. Assim, a legenda de blocos (BLOCO A/B/C) fica de fora.
- As cores da planta são as dos preenchimentos vetoriais. O código fica em `verificador/regras/setorizacao.py`.

| Código | Regra | Sev. | Resultado | Estado |
|---|---|---|---|---|
| PRA-12 | Planta geral de edificação sem legenda de setorização em nenhuma folha | ATENÇÃO | Acerta o 5420 (sem setorização). Nos 40 CEVs dispara em 26 documentos, 21 deles de projetos antigos (T015/T012) | **ativa** em todos os projetos (decisão da usuária em 30/10/2026) |
| PRA-13 | Cor do setor fora da paleta padrão | ERRO | Implementada | **ativa** desde 11/11/2026 (padrão aprovado, §22) |
| PRA-14 | Item da legenda sem uso na planta, ou mesma cor em dois itens | ERRO | 0 achados (todas as legendas coerentes) | **ativa** |
| PRA-15 | Nome fora da lista padrão de setores | ATENÇÃO | Implementada | lote 2, aguarda aprovação do padrão |
| PRA-16 | Cores muito parecidas na legenda (ΔE < 10) | ATENÇÃO | Dispara nas 6 legendas existentes (ΔE 4 a 8). Bate com o comentário "CORES MUITO PARECIDAS" do verificador no 6110-0001 | **ativa** |

## 20. Regras tiradas do CEV2 do 6110-0005 (30/10/2026)

**Material:** o CEV feito pela automação e o CEV2 feito pela verificadora sobre o mesmo documento (6110-0005 rev. B). O CEV2 tem cerca de 45 comentários.

**Comentários que viraram regra offline:**

| Código | Regra | Sev. | Comentário da verificadora | 40 CEVs | Estado |
|---|---|---|---|---|---|
| APR-12 | Título de vista só com o nível ("TÉRREO", "COBERTURA"), sem o tipo da vista | ATENÇÃO | "PLANTA BAIXA - TÉRREO (Ajustar no campo TITLE IN SHEET)" | 16 em 8 docs, mesmo padrão | **ativa** |
| APR-13 | Vistas da mesma faixa com títulos desalinhados (0,5 a 5 mm) | ATENÇÃO | "vistas desalinhadas" | 12 em 8 docs, sem comentário de verificador | lote 2 |
| TAB-07 | Linha de tabela encoberta por outro elemento, como o cabeçalho da tabela seguinte | ERRO | "tabelas desalinhadas, não dá para ler o texto" | 0 | **ativa** |
| CAR-14 | Código de emissão fora da tabela de Códigos de Emissão | ERRO | "porque PB? … favor ajustar para IN" | 0 | **ativa** |
| CON-05 | Cobertura ou corte sem largura/comprimento total das telhas (só em cobertura de telha) | ATENÇÃO | "comprimento/largura total telhas?? item obrigatório no check-list" (4×) | 11 em 8 docs | **ativa** |

**Mudança na leitura das vistas:**
- Um título só com o nível passou a valer como vista quando tem a linha de escala logo abaixo: "TÉRREO" vira PLANTA BAIXA, e "COBERTURA" vira COBERTURA.
- Antes, essas plantas eram ignoradas e as regras de vista não as avaliavam.
- Nos 40 CEVs, o único efeito foi 1 CON-02 a mais no 7610-0003.

**Comentários que ficaram para a versão Claude**, porque exigem interpretar o desenho. Foram acrescentados aos critérios RA:
- **RA-02:** altura total da edificação nas elevações e cortes (5×), balanço das telhas (2×) e altura dos fechamentos;
- **RA-03:** cota sobre o símbolo de corte ("conflito gráfico"), cotas pequenas ilegíveis e cota de nível mal posicionada;
- **RA-04:** perspectiva desproporcional à folha;
- **RA-05:** profundidade de vista;
- **RA-06:** área construída do Quadro × cotas externas e perímetro da tabela de telhas × desenho;
- **RA-07:** pendência listada no carimbo sem sinalização no desenho;
- **RA-01:** TAGs P2 e PI06;
- **RA-10:** questões técnicas (tela, viga metálica, pintura).

**Já coberto antes:** datas "XX/XX/26" (CAR-02 e PRA-10), título × LD (LD-05) e descida de água pluvial. A descida é a CON-03, que fica no lote 2 com mais esta evidência (2×).

**Leitura técnica:** a checagem "texto sob um preenchimento desenhado depois" pela ordem de desenho foi descartada, porque `get_texttrace` do PyMuPDF derruba o processo em alguns PDFs. A TAB-07 usa só a geometria.


## 21. Ajustes pedidos pela usuária (10/11/2026)

**Pedidos:**
1. pegar erros de ortografia e de digitação;
2. nos Documentos de Referência, conferir só o número, porque o título costuma ser resumido no projeto;
3. TAGs de ambiente preenchidas recebendo comentário de "falta PD" ou "faltam acabamentos";
4. apontar a falta de cotas: de nível, de dimensões dos ambientes e de altura do pé-direito (a lista veio incompleta);
5. conferir se existe a planta de setorização e se as cores estão corretas.

**Feito agora:**
- **LD-02 desativada (pedido 2).** Nos Documentos de Referência continuam o LD-01 (código não consta na LD, com sugestão do código parecido) e o LD-03 (documento excluído). O LD-05 (título do **carimbo** × LD) continua ativo, porque é o título do próprio documento.
- **Leitura das TAGs de ambiente (pedido 3).** Causa encontrada nos CEVs: acabamento de parede escrito como **"RE10/30"** ou **"RE30/34"** (dois revestimentos no mesmo campo). A regra exigia o código sozinho na linha, contava só 2 acabamentos e acusava a TAG completa. Mudanças em `tag_ambiente`:
  - os códigos de acabamento são contados **dentro** de cada linha (`RE10/30`, `PI-10`, `PI10A`, `PI10 TE30`);
  - a janela de busca cresce com o corpo do texto `A=` (TAG em escala maior) e gira com a TAG vertical;
  - o PD aceita também `PÉ-DIREITO` e `P.D.:`.

**Resultado nos 40 CEVs (lote 1):** 374 → 253 achados.

| Regra | Antes | Depois | Leitura |
|---|---|---|---|
| LD-02 | 117 | 0 | desativada |
| TAG-02 | 11 em 9 docs | 7 em 6 docs | os 4 que saíram eram falsos ("RE10/30") em 1310-0002, 1311-0001, 6110-0010 e 7610-0003 |
| TAG-01 | 7 em 7 docs | 7 em 7 docs | todos conferidos no desenho: as TAGs não têm PD |
| demais | — | iguais | — |

**Pendente, com perguntas à usuária:**
- **Ortografia (pedido 1):** proposta de regra nova com dicionário local (sem rede) e glossário técnico, só para palavras com correção próxima. Ver REL-01/VOC-02.
- **Cotas (pedido 4):** hoje só existe a CON-01 (vista sem nenhuma cota de nível). Faltam a lista completa e o critério de cada cota.
- **Setorização (pedido 5):** a PRA-12 (falta a planta-chave) está ativa e dispara corretamente nos 40 CEVs. A PRA-13 (cor fora do padrão) existe, mas está desligada até a aprovação do padrão, e só reconhece o setor pelo nome exato da lista. Nas legendas atuais, quase nenhum nome bate (REUNIÕES, COZINHA, BIBLIOTECA…).

## 22. Ortografia, cotas e cores da setorização (11/11/2026)

**Decisões da usuária (resposta ao §21):**
1. Ortografia com **dicionário + glossário** na versão offline e **apoio de IA** na versão Claude.
2. **Padrão de setorização aprovado** (`padroes/padrao-setorizacao.html`, `regras.json → setorizacao`).
3. Cotas aprovadas: nível em cada ambiente, dimensões dos ambientes, altura do pé-direito nos cortes e cotas entre eixos.
4. Os PDFs com os falsos comentários de TAG foram apagados; vale a correção do §21 (RE10/30).

**Regras novas e alteradas:**

| Código | Regra | Severidade | Resultado nos 40 CEVs | Estado |
|---|---|---|---|---|
| VOC-04 | Palavra desconhecida com correção próxima: "Verificar grafia: X — seria Y?". Um comentário por folha, com marca em cada ocorrência | ATENÇÃO | 64 achados em 32 docs, todos erros reais: CONUNTOS, ONUDLADA, ARUQUITETURA, SERVIÇOES, ESRTOCADOS, BERREIRA, TERRAPLEMAGEM, INSTUMENTAÇÃO, CRITÉTRIO, CORRESPONED, CARTACHO, ACABAMENTONA, BADEIRA, CONTENEDORES, PARADES, PERSPECITVA, DIIMENSÕES, NFRAESTRUTURA, EVESTIMENTO | **ativa** |
| PRA-13 | Cor do setor fora da paleta (ΔE > 3). Reconhece o setor pelo nome ou por um ambiente que ele inclui (COZINHA → OPERAÇÃO). Um comentário por legenda | ERRO | 4 legendas (6110-0001, 0002, 0011, 7610-0002), todas anteriores ao padrão | **ativa** |
| CON-08 | Corte sem cota vertical e sem texto de PD | ATENÇÃO | 1 (T015-1304-0001, CORTE C-C), com marca da verificadora | **ativa** |
| CON-06 | Ambiente sem cota de dimensão nas duas direções (faixa da TAG nas correntes de cota) | ATENÇÃO | 25 em 23 docs; amostra conferida: falsos | lote 2 |
| CON-07 | Ambiente sem cota de nível (EL.) perto da TAG | ATENÇÃO | 25 em 23 docs; amostra conferida: falsos | lote 2 |
| CON-04 | Cota entre eixos consecutivos | ATENÇÃO | 14 em 5 docs; acusou eixos já cotados (1310-0002, 6–7 com "600") | lote 2 |
| RA-14 | Versão Claude: ortografia e digitação, a partir dos achados VOC-04 | — | — | ativo |

**Por que CON-06 e CON-07 não foram ativadas:** nos projetos 6110, 7610, T012 e T015, a TAG de ambiente pequeno costuma ficar **fora do ambiente**, presa por uma linha de chamada, enquanto as cotas e o EL. ficam dentro do ambiente. A posição da TAG não diz onde o ambiente está. Amostras conferidas no desenho: T012-0211 (PORTARIA), T015-1304-0001 (ESCRITÓRIO, RACK), T015-1310-0002 (DML), 6110-0002 (DESCARTÁVEIS) e 7610-0002 (COPA, S. PCD). **Próximo passo:** seguir a linha de chamada (vetor que sai da TAG) até o ambiente. Até lá, o tema fica com a versão Claude (RA-02).

**Ortografia: como funciona a VOC-04.**
- Dicionário de português local: `pyspellchecker`, arquivo `pt.json.gz` embutido no exe, sem rede.
- Palavra conhecida = está no dicionário, no glossário técnico (`verificador/dic/glossario_tecnico.txt`, versionado), no glossário local (`glossario_local.txt` ao lado do `regras.json`, fora do Git, para nomes de pessoas) ou nos títulos da LD.
- Só aponta palavra com 5 letras ou mais, com correção a até 2 letras de distância. Sugere primeiro a forma do glossário (português do Brasil e termo técnico: TERRAPLENAGEM, PERSPECTIVA), depois a do dicionário.
- Diferença só de acento (NIVEL × NÍVEL) é ignorada, porque os verificadores não comentam. O carimbo fica de fora (nomes e texto em inglês).
- **Limite da validação:** o glossário foi montado a partir dos mesmos 40 CEVs, separando à mão os termos técnicos dos erros. Por isso a precisão medida aqui é otimista. Em projeto novo, termos e marcas ainda não vistos vão aparecer; basta acrescentá-los ao glossário.
- O dicionário mistura português do Brasil e de Portugal, por isso REGISTRO, CONTATO, SEÇÃO e ASPECTO estão no glossário.

**Total nos 40 CEVs (lote 1):** 253 → 322 achados (+64 VOC-04, +4 PRA-13, +1 CON-08).

## 23. Cotas do ambiente pela linha de chamada da TAG (11/11/2026)

**Pedido:** ativar as cotas de nível e de dimensão por ambiente, que o §22 deixou no lote 2 porque a TAG de ambiente pequeno fica fora do ambiente.

**Como ficou** (`regras/conteudo.py`, `TAG-comum.tag_ambiente.linha_chamada`):
- O contorno da TAG vai do nome ao PD, incluindo as pílulas dos códigos de acabamento.
- A linha de chamada é o segmento que sai do **topo ou da base, no eixo do nome**, ou de **uma lateral**. A regra segue os segmentos encadeados de mesma espessura e cor até a ponta. Entre as linhas que saem da TAG, fica o caminho contínuo mais longo, com pelo menos 15 pt; linha de eixo tracejada e contorno de pílula ficam curtos.
- A ponta é a posição do ambiente. Sem linha de chamada, vale a própria TAG.
- **CON-06:** cota horizontal na faixa de colunas e cota vertical na faixa de linhas da ponta, com meia-largura igual a √A pela escala da vista.
- **CON-07:** EL. num quadrado em volta da ponta ou da própria TAG. A segunda opção existe porque uma chamada de acabamento pode encostar na TAG.
- O texto é procurado em toda a folha, e não só no recorte da vista: no 6110-0002 o recorte cortava o "EL. 0,340" da CÂMARA REFRIGERADA.
- **Desempenho:** os vetores da folha (`get_drawings`) agora são lidos uma vez só (`Contexto.desenhos`) e compartilhados por setorização, composição e TAG.

**Resultado nos 40 CEVs:**

| Regra | §22 | Agora | Leitura |
|---|---|---|---|
| CON-06 | 25 em 23 docs | **2 em 2 docs** | ambos junto de marca da verificadora ("cotar largura da calçada" no 7610-0005) |
| CON-07 | 25 em 23 docs | **19 em 18 docs** | 11 junto de marca. Amostras conferidas no desenho: S. PCD e consultórios (7610-0002), PREP. - MASSAS (6110-0002), baias de resíduos (T015-1303), LABORATÓRIO (T015-1310), todos de fato sem EL. |

Pontas conferidas por imagem: DML (T015-1310-0002), PORTARIA e SANITÁRIO (T012-0211), DESCARTÁVEIS, CÂMARA REFRIGERADA e PREP. - MASSAS (6110-0002), ESCRITÓRIO (T015-1304-0001), COPA, S. PCD e CONSULTÓRIO 3 (7610-0002), SANIT. FEM. (6110-0011).

**Estado:** CON-06 e CON-07 **ativas**. A CON-04 (entre eixos) continua no lote 2.

**Total nos 40 CEVs (lote 1):** 322 → 343 achados.

