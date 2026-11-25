@echo off
rem Para o servidor e remove os atalhos (detalhes em ferramentas\desinstalar.ps1)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0ferramentas\desinstalar.ps1"
echo.
pause
