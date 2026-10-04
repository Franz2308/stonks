@echo off
echo ========================================================
echo   INICIANDO PLATAFORMA STONKS (SI642 Finanzas)
echo   Control de Cuenta Corriente y Credito de Barrio
echo ========================================================
echo.
python -c "import flask" 2>NUL
if errorlevel 1 (
    echo Instalando dependencias necesarias...
    pip install -r requirements.txt
)
echo Verificando base de datos y datos demo...
python -c "import database, seed_data; database.init_db();"
echo.
echo Servidor web iniciado en: http://localhost:5000
echo Presione CTRL+C para detener el servidor.
echo.
python app.py
pause
