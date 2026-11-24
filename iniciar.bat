@echo off
REM Abre el Sistema de Registro Documental en su propia ventana.
REM La ventana negra queda minimizada; se cierra sola al cerrar el sistema.
cd /d "%~dp0"
start "Registro Documental (no cerrar)" /min cmd /c "python app.py || pause"
