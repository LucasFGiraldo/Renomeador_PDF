@echo off
rem Instala o Renomeador de PDFs neste computador (detalhes em ferramentas\instalar.ps1)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0ferramentas\instalar.ps1"
if errorlevel 1 echo. & echo A instalacao NAO foi concluida. Veja a mensagem acima.
echo.
pause
