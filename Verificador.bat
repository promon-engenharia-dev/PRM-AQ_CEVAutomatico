@echo off
rem Arraste um ou mais PDFs sobre este arquivo (abre a janela com eles na lista), ou de dois cliques.
rem Processamento 100%% local: nenhum arquivo sai da maquina.
setlocal
cd /d "%~dp0"
if exist "%~dp0verificador.exe" (
    start "" "%~dp0verificador.exe" --janela %*
) else (
    start "" pythonw -X utf8 -m verificador --janela %*
)
