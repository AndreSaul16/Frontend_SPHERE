
# Script para arreglar el PATH de Podman en Windows
# Ejecutar con PowerShell

$ErrorActionPreference = "Stop"

Write-Host "🔍 Buscando instalación de Podman..." -ForegroundColor Cyan

# Posibles ubicaciones de podman.exe
$possiblePaths = @(
    "$env:ProgramFiles\RedHat\Podman\podman.exe",
    "$env:LOCALAPPDATA\Programs\Podman\bin\podman.exe",
    "$env:LOCALAPPDATA\Programs\Podman\podman.exe",
    "$env:UserProfile\podman\podman.exe"
)

$podmanPath = $null

foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        $podmanPath = $path
        break
    }
}

if ($null -eq $podmanPath) {
    Write-Error "❌ No se encontró podman.exe en las ubicaciones estándar. Por favor, verifica tu instalación."
    exit 1
}

$podmanDir = Split-Path -Parent $podmanPath
Write-Host "✅ Podman encontrado en: $podmanDir" -ForegroundColor Green

# Verificar si está en el PATH actual
if ($env:Path -like "*$podmanDir*") {
    Write-Host "✅ El directorio ya está en tu PATH actual." -ForegroundColor Green
    Write-Host "💡 Si no funciona, intenta reiniciar tu terminal o VS Code." -ForegroundColor Yellow
} else {
    Write-Host "⚠️ El directorio NO está en tu PATH actual." -ForegroundColor Yellow
    
    # Agregar al PATH persistente del usuario
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notlike "*$podmanDir*") {
        Write-Host "🔧 Agregando al PATH del usuario..." -ForegroundColor Cyan
        [Environment]::SetEnvironmentVariable("Path", "$userPath;$podmanDir", "User")
        Write-Host "✅ Agregado correctamente." -ForegroundColor Green
        Write-Host "🔄 IMPORTANTE: Reinicia tu terminal (y VS Code) para aplicar los cambios." -ForegroundColor Yellow
    } else {
        Write-Host "ℹ️ El directorio ya está en tu configuración de PATH de usuario, pero no en la sesión actual. Reinicia la terminal." -ForegroundColor Yellow
    }
}

Write-Host "`n🚀 Prueba ejecutando: podman --version (después de reiniciar)" -ForegroundColor Cyan
