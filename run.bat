@echo off
title Glow Up Cosmeticos - Gestion Comercial
chcp 65001 > nul
cd /d "%~dp0"
echo ================================================================
echo    GLOW UP COSMETICOS S.R.L. - SISTEMA DE GESTION COMERCIAL
echo            Opciones de Venta y Facturacion A (AFIP)
echo ================================================================
echo.

:: Verificar si Python esta instalado
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR CRITICO] Python no se encuentra instalado o no esta agregado al PATH.
    echo Por favor descarga e instala Python desde https://www.python.org/
    echo Recuerda marcar la casilla: [X] Add python.exe to PATH durante la instalacion.
    echo.
    pause
    exit /b
)

:: Verificar si las dependencias estan instaladas
python -c "import fastapi, uvicorn, jinja2" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Detectadas dependencias faltantes. Instalando automaticamente...
    echo.
    pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo [ERROR] No se pudieron instalar las dependencias con pip.
        pause
        exit /b
    )
    echo.
    echo Dependencias instaladas correctamente!
    echo.
)

echo Iniciando servidor en http://127.0.0.1:8000 ...
echo Puedes abrir tu navegador en: http://127.0.0.1:8000
echo Presione CTRL + C para detener el servidor.
echo.
python main.py
pause
