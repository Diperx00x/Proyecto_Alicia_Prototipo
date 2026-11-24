@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo   Instalacion del Sistema de Registro Documental - Version B
echo ============================================================
echo.
where python >nul 2>nul
if errorlevel 1 (
  echo [X] No se encontro Python.
  echo     Instale Python desde python.org y marque "Add Python to PATH".
  pause & exit /b 1
)
echo [1/3] Instalando librerias (Flask, PyMySQL, pywebview)...
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo [X] No se pudieron instalar las librerias. Revise la conexion a internet.
  pause & exit /b 1
)
echo.
echo [2/3] Creando la base de datos en MySQL...
python preparar_base.py
if errorlevel 1 ( pause & exit /b 1 )
echo.
echo [3/3] Datos de ejemplo
choice /c SN /m "Cargar datos de ejemplo para la defensa (usuario directora / clave demo123)"
if errorlevel 2 goto fin
python datos_demo.py
:fin
echo.
echo Listo. Para abrir el sistema: doble clic en iniciar.bat
pause
