# =============================================================================
# SPHERE — complete_test.ps1  (lanzador nativo para Windows / PowerShell)
#
# Ejecuta el harness de pruebas con curl (test/complete_test.sh) usando bash.
# Pensado para arrancar desde tu shell por defecto sin pelearte con la sintaxis.
#
# USO
#   .\test\complete_test.ps1
#   .\test\complete_test.ps1 -BaseUrl "http://localhost:8001/api/v1"
#   .\test\complete_test.ps1 -Token "eyJhbGci..."   # ID token Firebase real
#   .\test\complete_test.ps1 -Fast                  # omite el smoke de /stream
#
# REQUISITOS
#   - Backend corriendo (python backend/run_local.py). Para 'dev-token' arráncalo
#     con:  $env:ENVIRONMENT="development"; python backend/run_local.py
#   - bash disponible (Git Bash / WSL). En Win11 con Git instalado ya lo tienes.
# =============================================================================
[CmdletBinding()]
param(
    [string]$BaseUrl,
    [string]$Token,
    [switch]$Fast
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$shPath = Join-Path $scriptDir "complete_test.sh"

if (-not (Test-Path $shPath)) {
    Write-Error "No se encontró complete_test.sh junto a este script ($shPath)."
    exit 2
}

# Localizar bash (Git Bash / WSL / PATH)
$bash = (Get-Command bash -ErrorAction SilentlyContinue).Source
if (-not $bash) {
    foreach ($c in @("$env:ProgramFiles\Git\bin\bash.exe", "$env:ProgramFiles\Git\usr\bin\bash.exe", "$env:WINDIR\System32\bash.exe")) {
        if (Test-Path $c) { $bash = $c; break }
    }
}
if (-not $bash) {
    Write-Error "No se encontró 'bash'. Instala Git for Windows (incluye Git Bash) o usa WSL."
    exit 2
}

# Pasar parámetros como variables de entorno que el .sh ya consume
if ($BaseUrl) { $env:BASE_URL = $BaseUrl }
if ($Token)   { $env:SPHERE_TOKEN = $Token }
if ($Fast)    { $env:FAST = "1" }

# Convertir ruta Windows -> ruta estilo bash para evitar problemas de path
$shPathBash = $shPath -replace '\\', '/'

Write-Host "▶ Ejecutando harness con: $bash" -ForegroundColor Cyan
& $bash $shPathBash
exit $LASTEXITCODE
