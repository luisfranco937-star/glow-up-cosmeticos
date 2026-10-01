@echo off
title Glow Up Cosmeticos - Instalador
chcp 65001 > nul
echo ================================================================
echo    GLOW UP COSMETICOS S.R.L. - INSTALACION DE DEPENDENCIAS
echo ================================================================
echo.
echo Verificando e instalando librerias necesarias (FastAPI, Uvicorn, Jinja2)...
echo.
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] No se pudo completar la instalacion.
    echo Asegurate de tener Python instalado y activada la opcion 'Add python.exe to PATH'.
    pause
    exit /b
)
echo.
echo ================================================================
echo  INSTALACION FINALIZADA CON EXITO!
echo  Ahora puedes ejecutar directamente 'run.bat' para abrir el sistema.
echo ================================================================
echo.
pause
