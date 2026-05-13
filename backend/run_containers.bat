@echo off
REM SPHERE Backend — Run with Podman (Windows)
REM Usage: run_containers.bat

echo.
echo ========================================
echo   SPHERE Backend - Podman
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
    echo Edita .env con tus credenciales antes de continuar.
    echo Variables obligatorias:
    echo   - MONGODB_URL
    echo   - DEEPSEEK_API_KEY
    echo   - OPENAI_API_KEY
    echo   - FERNET_KEY
    echo   - FIREBASE_CREDENTIALS_PATH
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
echo   SPHERE Backend esta listo!
echo ========================================
echo.
echo   Backend:  http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo   MongoDB:  http://localhost:27017
echo   Redis:    http://localhost:6379
echo   n8n:      http://localhost:5678
echo.
echo   Para ver logs: podman-compose logs -f
echo   Para parar:    podman-compose down
echo.
pause
