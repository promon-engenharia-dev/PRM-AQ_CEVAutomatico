# Padrão visual Promon aplicado

A fonte é `../promon-parametros-formatacao.md`, que fica fora do repositório, na pasta 02.07_Ferramentas. Leia o original antes de mudanças grandes na interface.

## Cores e fonte

- **Cores claras:** fundo `#EDF1F4`, azul `#004976` (títulos e botão principal), texto `#333F48`, secundário `#7C878E`.
- **Laranja:** `#E35205` só como acento (filete, marcador de seção). Texto laranja pequeno usa `#BE531C`.
- **Escuro:** tokens do MD §2.1, aplicados por `prefers-color-scheme` no HTML e por `AppsUseLightTheme` (só leitura) no Tkinter.
- **Fonte:** `'Soleto','Mulish',Tahoma,Arial,sans-serif`.

## Componentes

- **Cabeçalho (MD §7.1):** logo oficial com 30 px de altura e área de proteção x/2, régua vertical, título 18 px peso 800 em azul, subtítulo 11,5 px.
  - Logo positivo no modo claro, negativo no escuro, em `verificador/web/img/`.
  - Título: "Verificador de Projetos — Arquitetura".
- **Sombra:** uma única, `0 1px 2px rgba(16,42,67,.04)`.
- **Estados:** ERRO e ATENÇÃO sempre escritos por extenso, com a cor de estado e peso 800.
- **Cartões de números:** com sublegenda.

## Restrições

- Nada carregado da internet: sem CDN e sem fontes web remotas.
- O relatório HTML é um arquivo único, com imagens em base64.
- Imagens novas da interface precisam entrar no `--add-data` do `ferramentas\gerar_exe.bat`.
