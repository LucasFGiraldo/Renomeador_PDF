# Instala o Renomeador de PDFs neste computador (chamado pelo instalar.bat).
#  1. instala as dependencias Python
#  2. liga o servidor sozinho quando o usuario entra no Windows (sem janela)
#  3. cria o atalho "Renomeador de PDFs" na Area de Trabalho
#  4. liga o servidor agora e abre o sistema no navegador
# Nao precisa de administrador. (Arquivo sem acentos de proposito: o
# PowerShell do Windows le .ps1 sem BOM com outra codificacao.)

$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host ''
Write-Host 'Instalando o Renomeador de PDFs...'

# Python
try {
    $python = (& python -c "import sys; print(sys.executable)").Trim()
} catch {
    throw 'Python nao encontrado. Instale o Python (python.org) marcando "Add Python to PATH" e rode de novo.'
}
$pythonw = Join-Path (Split-Path -Parent $python) 'pythonw.exe'
if (-not (Test-Path $pythonw)) { throw "pythonw.exe nao encontrado ao lado de $python" }

# Arquivo de caminhos (nao vem pelo GitHub)
if (-not (Test-Path (Join-Path $raiz 'config.py'))) {
    throw 'Falta o arquivo config.py com os caminhos das pastas (veja o README).'
}

Write-Host '- Instalando dependencias (pode levar um minuto)...'
& $python -m pip install --quiet --disable-pip-version-check -r (Join-Path $raiz 'requisitos.txt')
if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar as dependencias.' }

$shell = New-Object -ComObject WScript.Shell
$api = Join-Path $raiz 'api.py'
$abrir = Join-Path $raiz 'ferramentas\abrir.py'

Write-Host '- Configurando para iniciar junto com o Windows...'
$inicializar = Join-Path ([Environment]::GetFolderPath('Startup')) 'Renomeador de PDFs (servidor).lnk'
$lnk = $shell.CreateShortcut($inicializar)
$lnk.TargetPath = $pythonw
$lnk.Arguments = '"' + $api + '"'
$lnk.WorkingDirectory = $raiz
$lnk.Description = 'Servidor local do Renomeador de PDFs'
$lnk.Save()

Write-Host '- Criando o atalho na Area de Trabalho...'
$atalho = Join-Path ([Environment]::GetFolderPath('Desktop')) 'Renomeador de PDFs.lnk'
$lnk = $shell.CreateShortcut($atalho)
$lnk.TargetPath = $pythonw
$lnk.Arguments = '"' + $abrir + '"'
$lnk.WorkingDirectory = $raiz
$lnk.IconLocation = "$env:SystemRoot\System32\shell32.dll,54"
$lnk.Description = 'Abre o Renomeador de PDFs no navegador'
$lnk.Save()

Write-Host '- Ligando o sistema e abrindo o navegador...'
Start-Process -FilePath $pythonw -ArgumentList ('"' + $abrir + '"') -WorkingDirectory $raiz

Write-Host ''
Write-Host 'Pronto! Use o atalho "Renomeador de PDFs" da Area de Trabalho.'
Write-Host 'O sistema liga sozinho sempre que voce entrar no Windows.'
