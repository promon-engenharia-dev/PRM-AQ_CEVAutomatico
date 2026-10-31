@echo off
rem Gera dist\VerificadorCEV\ com o executavel unico (PyInstaller), o Verificador.bat e o regras.json.
rem Requisitos so na maquina que gera: Python 3.10+, pip install -r requirements.txt pyinstaller
setlocal
cd /d "%~dp0.."
set TRABALHO=%TEMP%\VerificadorCEV_build
set DESTINO=dist\VerificadorCEV

python -m PyInstaller --noconfirm --clean --onefile --windowed ^
    --name verificador ^
    --workpath "%TRABALHO%" --specpath "%TRABALHO%" --distpath "%DESTINO%" ^
    --paths "%CD%" ^
    --add-data "%CD%\regras.json;." ^
    --add-data "%CD%\verificador\web;verificador\web" ^
    --collect-submodules verificador ^
    --exclude-module numpy --exclude-module matplotlib --exclude-module pandas ^
    ferramentas\entrada_exe.py
if errorlevel 1 exit /b 1

copy /y Verificador.bat "%DESTINO%\" >nul
copy /y regras.json "%DESTINO%\" >nul
copy /y ferramentas\LEIA-ME_distribuicao.txt "%DESTINO%\LEIA-ME.txt" >nul
echo.
echo Pronto: %DESTINO%
