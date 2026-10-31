# Formato do `<nome>.revisao.json`

O arquivo é lido por `verificador/revisao.py` (opção `--revisao`).

```json
{
  "versao": 1,
  "criterio_projeto": "caminho do critério usado, ou null",
  "achados": [
    {
      "regra": "RA-08",
      "severidade": "ERRO",
      "folha": 1,
      "ancora": "PI11",
      "todas_ocorrencias": false,
      "titulo": "Piso da área molhada diferente do critério",
      "comentario": "PI11 (porcelanato polido) na Copa; o critério pede piso antiderrapante em áreas molhadas.",
      "acao": "Trocar para revestimento antiderrapante (PI10).",
      "base": "Critério de Projeto §6.2, p. 14"
    }
  ]
}
```

## Campos

| Campo | Obrigatório | Regra |
|---|---|---|
| `regra` | sim | Código existente em `regras.json → revisao_assistida.criterios`. Senão, o achado é ignorado com aviso |
| `severidade` | sim | `ERRO`, `ATENCAO` ou `CORRETO` |
| `folha` | sim | 1 = primeira página do PDF |
| `ancora` | um dos dois | Texto que aparece na folha (comparado sem acento e sem diferença de caixa). A 1ª linha que contém o texto é o alvo |
| `retangulo_mm` | um dos dois | `[x0, y0, x1, y1]` em mm na folha como exibida, origem no canto superior esquerdo. Marca uma área (retângulo translúcido) |
| `todas_ocorrencias` | não | `true` marca todas as linhas que contêm a âncora na folha |
| `titulo` | recomendado | Uma linha. Aparece no relatório, não no PDF |
| `comentario` | sim | O que está errado ou o que foi conferido |
| `acao` | não | O que fazer. No PDF, entra depois de "→ " |
| `base` | recomendado | Fonte. No PDF, entra como "(Base: …)" |

## Como vira anotação

- **No PDF:** uma caixa vermelha `CV-AQ-nnn` com `comentario → acao (Base: base)`, mais faixa ou retângulo e seta, igual aos achados offline. A numeração é única para os achados offline e os do Claude.
- **CORRETO:** não vai para o PDF. Aparece no relatório e no CSV, com índice "—".
- **No relatório e no CSV:** a origem é "Revisão assistida" (`origem = claude`).
- **Âncora não encontrada:** o achado vai para o carimbo, com aviso. Corrija a âncora e rode de novo.
