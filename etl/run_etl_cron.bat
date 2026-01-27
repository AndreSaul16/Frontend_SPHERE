@echo off
REM ============================================================
REM SPHERE ETL - Script de Ejecución Periódica (CRON)
REM ============================================================
REM Este script ejecuta el ETL del CTO de forma automatizada
REM Incluye gestión de logs y activación de entorno Conda

REM Cambiar al directorio del proyecto
cd /d C:\Users\Saul\Documents\PROGRAMACION\SPHERE\etl

REM Activar entorno Conda (base o el que uses)
call conda activate base

REM Crear directorio de logs si no existe
if not exist "logs" mkdir logs

REM Generar nombre de archivo de log con timestamp
set TIMESTAMP=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set LOGFILE=logs\etl_cron_%TIMESTAMP%.log

REM Ejecutar ETL y redirigir output al log
echo ================================================ >> %LOGFILE%
echo SPHERE ETL - Ejecución Automática >> %LOGFILE%
echo Fecha: %date% %time% >> %LOGFILE%
echo ================================================ >> %LOGFILE%

python run_etl.py --agent cto >> %LOGFILE% 2>&1

REM Guardar código de salida
set EXITCODE=%ERRORLEVEL%

echo. >> %LOGFILE%
echo ================================================ >> %LOGFILE%
echo Ejecución finalizada. Código de salida: %EXITCODE% >> %LOGFILE%
echo ================================================ >> %LOGFILE%

REM Mostrar mensaje en consola (opcional, para debug)
echo ETL ejecutado. Ver log: %LOGFILE%

exit /b %EXITCODE%
