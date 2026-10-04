@echo off
setlocal
cd /d "%~dp0"

echo ========================================================
echo   INICIANDO PLATAFORMA STONKS (SI642 Finanzas)
echo   Control de Cuenta Corriente y Credito de Barrio
echo ========================================================
echo.

:: 1. Detectar comando de Python disponible
set "PY_CMD="
py --version >nul 2>nul
if not errorlevel 1 (
    set "PY_CMD=py"
) else (
    python --version >nul 2>nul
    if not errorlevel 1 (
        set "PY_CMD=python"
    )
)

if "%PY_CMD%"=="" goto :no_python

:: 2. Verificar dependencias
echo [1/3] Verificando dependencias...
%PY_CMD% -c "import flask" >nul 2>nul
if errorlevel 1 (
    echo Instalando paquetes necesarios: Flask y dependencias...
    %PY_CMD% -m pip install -r requirements.txt
    if errorlevel 1 goto :pip_error
)

:: 3. Base de datos
echo [2/3] Verificando base de datos y perfiles demo...
%PY_CMD% -c "import database, seed_data; database.init_db(); conn = database.get_db_connection(); c = conn.cursor().execute('SELECT count(*) FROM usuarios').fetchone()[0]; conn.close(); seed_data.seed() if c == 0 else None"

:: 4. Servidor
echo [3/3] Iniciando servidor web en http://localhost:5000...
echo.
echo ========================================================
echo   STONKS esta listo.
echo   Se abrira su navegador web automaticamente.
echo   Para cerrar el servidor, presione CTRL+C.
echo ========================================================
echo.

start http://localhost:5000
%PY_CMD% app.py
goto :eof

:no_python
echo.
echo ========================================================
echo   ERROR: No se encontro Python en su sistema.
echo ========================================================
echo Por favor descargue e instale Python 3.10 o superior desde:
echo https://www.python.org/downloads/
echo.
echo IMPORTANTE: En el instalador, marque la casilla:
echo    "Add python.exe to PATH"
echo.
pause
exit /b 1

:pip_error
echo.
echo ========================================================
echo   ERROR al instalar paquetes con pip.
echo ========================================================
echo Verifique su conexion a internet e intente nuevamente.
echo.
pause
exit /b 1
