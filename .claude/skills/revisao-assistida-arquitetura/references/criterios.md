# Critérios da revisão assistida (RA)

Os códigos e nomes oficiais estão em `regras.json → revisao_assistida.criterios`. Este arquivo explica o que conferir em cada um. Os critérios RA-01 a RA-05 e RA-11 cobrem o que a versão offline deixa fora de escopo (ver `cev-arquitetura/references/fora-de-escopo.md`).

| Código | O que conferir | Onde olhar |
|---|---|---|
| RA-01 TAG faltando | Elementos sem TAG: esquadrias (porta PM, janela JA), louças e metais (HD), revestimentos de piso, parede e teto por ambiente, bancadas, calha e rufo. Também TAG apontando para o elemento errado | Planta e cortes × tabelas da folha |
| RA-02 Cota ou nível faltando | PD na TAG do ambiente e no corte, entreforro, peitoril de janela, altura de bancada, níveis de piso acabado e calçada, cotas entre eixos e total, amarração de esquadrias. **Altura total da edificação** nas elevações e cortes, **balanço das telhas**, **altura dos fechamentos** (CEV2 6110-0005) | Plantas, cortes e elevações |
| RA-03 Conflito gráfico | Texto sobre traço ou hachura, cota sobre parede ou símbolo de corte, TAG sobreposta, linha de chamada cruzando texto, **cotas pequenas ilegíveis** (deslocar), **cota de nível mal posicionada** | Recortes ampliados |
| RA-04 Organização da folha | Título longe ou desalinhado da vista, **vistas da mesma faixa desalinhadas** (APR-13 ajuda), vistas apertadas, tabelas fora de ordem, **perspectiva desproporcional à folha**, espaço mal usado | Visão geral |
| RA-05 Representação | Hachura sem legenda ou legenda sem uso, halftone e espessuras, profundidade de vista, simbologia diferente da legenda | Legenda × desenho |
| RA-06 Coerência entre vistas | Planta × corte × elevação: PD, níveis, esquadrias (posição, dimensão, quantidade), eixos, cobertura (viga, telha, calha). Área da TAG × cotas. **Área construída do Quadro de Áreas × cotas externas**. Quantidades nas tabelas (ex.: perímetro de calhas, telhas) × elementos desenhados | Todas as vistas e tabelas |
| RA-07 Notas × desenho | Nota que contradiz o desenho, nota que remete a folha ou documento inexistente, nota genérica que não se aplica. **Pendência listada no carimbo sem sinalização (nuvem/indicação) no desenho** | Notas gerais e desenho |
| RA-08 Critério de projeto | Sistema construtivo, materiais, acabamentos por tipo de ambiente, PD mínimo, módulos e dimensões, cobertura e inclinação, impermeabilização, esquadrias padrão, acessibilidade exigida | `criterio_projeto.txt` × folha |
| RA-09 Normas | NBR 9050 (barras de apoio, área de giro, alturas de louças e acessórios, porta de 80 cm livre), segurança contra incêndio e saídas, ventilação e iluminação natural, NR-24 (vestiários e sanitários), NR aplicáveis | Ampliações, sanitários, rotas |
| RA-10 Solução de projeto | Drenagem e caimentos, impermeabilização de áreas molhadas, interface entre materiais, compatibilização com disciplinas (pilares, shafts, descidas pluviais), durabilidade | Desenho e tabelas |
| RA-11 Escala | Escala inadequada à leitura (muito pequena para o detalhe) ou carimbo × vistas | Títulos de vista e carimbo |
| RA-12 CheckList AQ | Itens do `referencias/CheckList Arquitetura.xlsx` verificáveis na folha que não têm regra offline ativa | CheckList × folha |
| RA-13 Planta-chave de setorização | Em documento com planta geral, há planta-chave de layout/departamentos com legenda? A legenda segue o padrão: título SETORIZAÇÃO, setores da lista fechada, cor de cada setor (`regras.json → setorizacao`), ordem fixa, nomes completos, cor lisa? Legenda × planta: todo setor colorido está na legenda e vice-versa? A área por setor bate com o Quadro de Áreas? | Planta-chave × legenda × `padroes/padrao-setorizacao.html` |
| RA-14 Ortografia e digitação | Comece pelos achados **VOC-04** da versão offline e confirme cada um. Depois leia todo o texto da folha e aponte o que o dicionário não pega: palavra que existe mas está errada no contexto (SESSÃO × SEÇÃO, CONCERTO × CONSERTO), letra trocada que forma outra palavra, concordância ("PAREDES INTERNO"), acentuação incorreta (fora das maiúsculas sem acento, que o verificador aceita), termo técnico mal escrito e abreviação fora do padrão do projeto. Cite a forma correta | Notas, tabelas, títulos, TAGs, Documentos de Referência |

## Severidade

- **ERRO:** divergência objetiva. Por exemplo, a TAG não existe na tabela, o desenho contradiz o critério de projeto, ou o valor está fora de uma norma citada com a fonte.
- **ATENÇÃO:** depende de confirmação, ou é questão de projeto ou interpretação.
- **CORRETO:** conferência relevante que passou. Por exemplo, a área bate com as cotas, ou o sanitário PCD atende às barras exigidas.
