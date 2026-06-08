# ============================================
# SPHERE v3-TheLastDance — Deploy Express
# Ejecutar desde PowerShell como Admin
# ============================================
param(
    [switch]$SkipLogin,
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    # Nombres EXACTOS de los servicios en Railway (proyecto SPHERE). El servicio
    # linkado por defecto puede ser otro (p.ej. n8n), por eso targeteamos siempre
    # por --service y NO confiamos en `railway up` a secas.
    [string]$BackendService = "Backend_SHPERE",
    [string]$FrontendService = "Frontend_SPHERE",
    [string]$Message = "v3: CI/CD pipeline + Ragnarok production fixes"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SPHERE v3 — The Last Dance Deploy" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ── Step 0: Check Railway CLI ──
Write-Host "[0/4] Checking Railway CLI..." -ForegroundColor Yellow
$railway = Get-Command railway -ErrorAction SilentlyContinue
if (-not $railway) {
    Write-Host "  Railway CLI not found. Installing..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri https://cli.new -UseBasicParsing | Invoke-Expression
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Write-Host "  Railway CLI installed. You may need to restart your terminal after this script." -ForegroundColor Green
} else {
    Write-Host "  Railway CLI found: $(railway --version)" -ForegroundColor Green
}

# ── Step 1: Login ──
if (-not $SkipLogin) {
    Write-Host ""
    Write-Host "[1/4] Logging into Railway..." -ForegroundColor Yellow
    Write-Host "  A browser window will open. Log in with your Railway account." -ForegroundColor White
    railway login
    Write-Host "  Logged in." -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "[1/4] Skipping login (--SkipLogin flag)" -ForegroundColor Yellow
}

# ── Step 2: Deploy Backend ──
if (-not $FrontendOnly) {
    Write-Host ""
    Write-Host "[2/4] Deploying Backend -> $BackendService ..." -ForegroundColor Yellow
    Push-Location "$Root\backend"
    try {
        railway up --detach --service $BackendService -m "$Message [backend]"
        if ($LASTEXITCODE -ne 0) { throw "railway up devolvio exit code $LASTEXITCODE" }
        Write-Host "  Backend deploy triggered -> $BackendService" -ForegroundColor Green
    } catch {
        Write-Host "  Backend deploy FAILED: $_" -ForegroundColor Red
        Pop-Location
        throw
    }
    Pop-Location
}

# ── Step 3: Deploy Frontend ──
if (-not $BackendOnly) {
    Write-Host ""
    Write-Host "[3/4] Deploying Frontend -> $FrontendService ..." -ForegroundColor Yellow
    Push-Location "$Root\frontend"
    try {
        railway up --detach --service $FrontendService -m "$Message [frontend]"
        if ($LASTEXITCODE -ne 0) { throw "railway up devolvio exit code $LASTEXITCODE" }
        Write-Host "  Frontend deploy triggered -> $FrontendService" -ForegroundColor Green
    } catch {
        Write-Host "  Frontend deploy FAILED: $_" -ForegroundColor Red
        Pop-Location
        throw
    }
    Pop-Location
}

# ── Step 4: Status ──
Write-Host ""
Write-Host "[4/4] Checking deployment status..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
try {
    # `railway service status` quedó deprecado; `railway status` da el overview
    # de servicios + URLs + estado online, y funciona en PowerShell 5.1.
    railway status
} catch {
    Write-Host "  Could not fetch status: $_" -ForegroundColor Yellow
    Write-Host "  Check: https://railway.com/dashboard" -ForegroundColor Yellow
}

# ── Done ──
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Deploy triggered. Monitor at:" -ForegroundColor Cyan
Write-Host "  https://railway.com/dashboard" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Health checks:" -ForegroundColor White
Write-Host "  Backend:  curl <backend-url>/api/v1/health/live" -ForegroundColor Gray
Write-Host "  Frontend: curl <frontend-url>/" -ForegroundColor Gray
