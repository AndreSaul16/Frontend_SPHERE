@echo off
REM SPHERE Frontend — Run with Podman (Windows)
REM Usage: run_containers.bat

echo.
echo ========================================
echo   SPHERE Frontend - Podman
echo ========================================
echo.

REM Check if podman is installed
where podman >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Podman no esta instalado.
    echo Descarga: https://podman.io/getting-started/installation
    exit /b 1
)

REM Check if .env exists
if not exist .env (
    echo ADVERTENCIA: Archivo .env no encontrado.
    echo Copiando .env.example a .env...
    copy .env.example .env
    echo.
    echo Edita .env con tus credenciales de Firebase antes de continuar.
    echo.
    pause
)

echo Iniciando contenedores...
echo.

REM Build and start
podman-compose up -d --build

echo.
echo Esperando que los servicios arranquen...
timeout /t 10 /nobreak >nul

echo.
echo Estado de los servicios:
podman-compose ps

echo.
echo ========================================
echo   SPHERE Frontend esta listo!
echo ========================================
echo.
echo   Frontend: http://localhost:3000
echo.
echo   Para ver logs: podman-compose logs -f
echo   Para parar:    podman-compose down
echo.
pause
