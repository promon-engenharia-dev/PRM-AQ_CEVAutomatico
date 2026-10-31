# Validação de regras

## Material (local, fora do Git)

- `referencias/CEV-Referencias/`: os CEVs de referência de Arquitetura, PDFs já verificados por pessoas, com comentários vermelhos.
- `referencias/originais/`: PDFs sem CEV, para testar como o operador vai usar.
- LDs `*-PL2-*.xlsx` das operações, quando houver.

## Como rodar

```bash
python -X utf8 ferramentas/validar_referencias.py --lote 2    # inclui regras do lote 2 sem ativá-las
python -X utf8 -m verificador --lote 2 --sem-formulario arquivo.pdf
```

O validador roda o verificador em cada CEV e, para cada achado, procura uma marca vermelha humana num raio de **15 mm**. Ele considera as anotações e também os comentários de rodadas anteriores que foram achatados no conteúdo. A saída fica em `saida_teste/validacao.csv` e `saida_teste/validacao_resumo.txt`.

## Como ler os números

- **"Perto de uma marca vermelha" não prova acerto:** a marca pode ser sobre outra coisa. Confira o texto do comentário humano mais próximo, que vem no CSV.
- **"Sem marca" não prova falso positivo:** o verificador pode não ter comentado. Liste esses casos para o usuário conferir.
- **Volume de referência do lote 1:** cerca de 2,4 achados por documento. Uma regra que multiplica esse volume sem casar com comentários humanos é ruído.
- **Mostre ao usuário, por regra:** número de achados, número de documentos, quantos casam com comentário humano e exemplos.

## Armadilhas já encontradas

- **Comentários achatados no conteúdo:** comentários de rodadas anteriores e o carimbo "Cópia de Verificação" ficam no conteúdo da página. Sem filtro (`filtros.conteudo`), a ferramenta comentaria os próprios comentários.
- **Anotações SHX:** anotações `/Square` "AutoCAD SHX Text" aparecem às centenas e são filtradas pelo autor.
- **Páginas giradas:** use as coordenadas de exibição (`rotation_matrix`).
- **Carimbos sobrepostos:** texto novo sobre texto antigo no carimbo é resolvido por caractere em `carimbo.juntar`.
- **Tabelas vizinhas:** cada linha pertence ao título de tabela mais próximo (`_dono`).
- **Repetição por folha:** carimbo e lista de referências se repetem em cada folha, o que multiplica os achados.

## Confidencialidade

Não copie trechos, números de documento ou nomes de cliente dos PDFs de referência para código, testes, catálogo ou para esta skill. Os resultados de teste ficam em `saida_teste/`, que não é versionada.
