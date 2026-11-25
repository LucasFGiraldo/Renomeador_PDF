# Desfaz o instalar.ps1: para o servidor e remove os atalhos.
# Nao apaga nenhum arquivo do projeto, nem PDFs, nem historico.

$ErrorActionPreference = 'Continue'

Write-Host ''
Write-Host 'Removendo o Renomeador de PDFs da inicializacao...'

Get-CimInstance Win32_Process -Filter "Name='pythonw.exe' OR Name='python.exe'" |
    Where-Object { $_.CommandLine -like '*api.py*' } |
    ForEach-Object {
        Write-Host "- Parando o servidor (processo $($_.ProcessId))"
        Stop-Process -Id $_.ProcessId -Force
    }

foreach ($arquivo in @(
    (Join-Path ([Environment]::GetFolderPath('Startup')) 'Renomeador de PDFs (servidor).lnk'),
    (Join-Path ([Environment]::GetFolderPath('Desktop')) 'Renomeador de PDFs.lnk')
)) {
    if (Test-Path $arquivo) {
        Remove-Item $arquivo
        Write-Host "- Removido: $arquivo"
    }
}

Write-Host ''
Write-Host 'Pronto. Para instalar de novo, rode o instalar.bat.'
