# Automatización del ETL - SPHERE

Este documento explica cómo configurar la ejecución periódica (automática) del ETL del sistema SPHERE.

## 📋 Tabla de Contenidos

- [Windows - Tareas Programadas](#windows---tareas-programadas)
- [Linux/Mac - Cron](#linuxmac---cron)
- [Ejecución Manual](#ejecución-manual)
- [Gestión de Logs](#gestión-de-logs)

---

## Windows - Tareas Programadas

### Opción 1: Interfaz Gráfica (Recomendado)

1. **Abrir Programador de Tareas**:
   - Presionar `Win + R`
   - Escribir `taskschd.msc` y presionar Enter

2. **Crear Nueva Tarea**:
   - Click derecho en "Biblioteca del Programador de Tareas"
   - Seleccionar "Crear tarea..."

3. **Configurar Tarea**:
   
   **Pestaña General**:
   - Nombre: `SPHERE ETL - CTO`
   - Descripción: `Ejecución periódica del ETL para datos del CTO`
   - Ejecutar con los privilegios más altos: ✅ (opcional)
   
   **Pestaña Desencadenadores**:
   - Nuevo → Programación
   - Configurar frecuencia (ejemplos):
     - **Diario**: Todos los días a las 2:00 AM
     - **Semanal**: Todos los domingos a las 3:00 AM
     - **Mensual**: El primer día del mes a las 1:00 AM
   
   **Pestaña Acciones**:
   - Acción: `Iniciar un programa`
   - Programa: `C:\Users\Saul\Documents\PROGRAMACION\SPHERE\etl\run_etl_cron.bat`
   - Iniciar en: `C:\Users\Saul\Documents\PROGRAMACION\SPHERE\etl`
   
   **Pestaña Condiciones**:
   - Iniciar solo si el equipo está conectado a la alimentación de CA: ✅ (opcional)
   - Despertar el equipo para ejecutar esta tarea: ❌

4. **Guardar y Probar**:
   - Click derecho en la tarea creada → "Ejecutar"
   - Verificar el archivo de log en `etl/logs/`

### Opción 2: PowerShell

```powershell
# Crear tarea que se ejecuta todos los días a las 2:00 AM
$action = New-ScheduledTaskAction -Execute "C:\Users\Saul\Documents\PROGRAMACION\SPHERE\etl\run_etl_cron.bat"
$trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName "SPHERE ETL - CTO" -Action $action -Trigger $trigger -Settings $settings -Description "Ejecución periódica del ETL para datos del CTO"
```

---

## Linux/Mac - Cron

### 1. Crear Script Ejecutable

Primero, crea el script `run_etl_cron.sh`:

```bash
#!/bin/bash
# SPHERE ETL - Script de Ejecución Periódica

cd /path/to/SPHERE/etl

# Activar entorno virtual (ajustar según tu setup)
source ~/.bashrc
conda activate base

# Crear directorio de logs
mkdir -p logs

# Generar nombre de log con timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOGFILE="logs/etl_cron_$TIMESTAMP.log"

# Ejecutar ETL
echo "===============================================" >> $LOGFILE
echo "SPHERE ETL - Ejecución Automática" >> $LOGFILE
echo "Fecha: $(date)" >> $LOGFILE
echo "===============================================" >> $LOGFILE

python run_etl.py --agent cto >> $LOGFILE 2>&1

echo "" >> $LOGFILE
echo "Ejecución finalizada. Código: $?" >> $LOGFILE
echo "===============================================" >> $LOGFILE
```

Hacer ejecutable:
```bash
chmod +x /path/to/SPHERE/etl/run_etl_cron.sh
```

### 2. Configurar Cron

Editar crontab:
```bash
crontab -e
```

Añadir una de estas líneas según la frecuencia deseada:

```cron
# Ejecutar todos los días a las 2:00 AM
0 2 * * * /path/to/SPHERE/etl/run_etl_cron.sh

# Ejecutar todos los domingos a las 3:00 AM
0 3 * * 0 /path/to/SPHERE/etl/run_etl_cron.sh

# Ejecutar el primer día de cada mes a las 1:00 AM
0 1 1 * * /path/to/SPHERE/etl/run_etl_cron.sh

# Ejecutar cada 6 horas
0 */6 * * * /path/to/SPHERE/etl/run_etl_cron.sh
```

### 3. Verificar Cron

Listar tareas programadas:
```bash
crontab -l
```

Ver logs del sistema cron:
```bash
grep CRON /var/log/syslog  # Ubuntu/Debian
grep CRON /var/log/cron    # CentOS/RHEL
```

---

## Ejecución Manual

Para ejecutar el ETL manualmente (para probar):

### Windows
```cmd
cd C:\Users\Saul\Documents\PROGRAMACION\SPHERE\etl
run_etl_cron.bat
```

### Linux/Mac
```bash
cd /path/to/SPHERE/etl
./run_etl_cron.sh
```

### Con Python directamente
```bash
cd etl
python run_etl.py --agent cto
```

### Ejecutar spiders individuales
```bash
# Solo descargar PDFs de ArXiv
python run_etl.py --spider arxiv_pdfs

# Solo integrar libros sintéticos
python run_etl.py --spider books

# Solo GitHub
python run_etl.py --spider github
```

---

## Gestión de Logs

### Ubicación de Logs

Todos los logs se guardan en: `etl/logs/`

Formato de nombre: `etl_cron_YYYYMMDD_HHMMSS.log`

Ejemplo: `etl_cron_20260115_020000.log`

### Ver Último Log

**Windows**:
```cmd
cd etl\logs
dir /O-D | more
type etl_cron_*.log | more
```

**Linux/Mac**:
```bash
cd etl/logs
ls -lt | head
tail -n 100 etl_cron_*.log
```

### Limpiar Logs Antiguos

**Manualmente**:
```bash
# Eliminar logs de más de 30 días (Linux/Mac)
find etl/logs -name "etl_cron_*.log" -mtime +30 -delete

# Windows (PowerShell)
Get-ChildItem etl\logs -Filter "etl_cron_*.log" | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-30)} | Remove-Item
```

**Automatizado (añadir al script)**:

En `run_etl_cron.bat` (Windows), añadir antes de la ejecución:
```batch
REM Limpiar logs de más de 30 días
forfiles /p logs /s /m etl_cron_*.log /d -30 /c "cmd /c del @path" 2>nul
```

En `run_etl_cron.sh` (Linux/Mac), añadir:
```bash
# Limpiar logs de más de 30 días
find logs -name "etl_cron_*.log" -mtime +30 -delete
```

---

## Monitoreo y Alertas

### Verificar Ejecución Exitosa

Buscar en el log la línea:
```
✅ EJECUCIÓN COMPLETADA
```

### Alertas por Email (Opcional)

Para configurar alertas por email en caso de fallo:

**Windows** (usando PowerShell en el script):
```powershell
if ($LASTEXITCODE -ne 0) {
    Send-MailMessage -To "admin@example.com" -From "etl@sphere.com" -Subject "ETL Failure" -Body "Ver log: $LOGFILE" -SmtpServer "smtp.example.com"
}
```

**Linux/Mac** (usando mailx):
```bash
if [ $? -ne 0 ]; then
    echo "ETL failed. Ver log: $LOGFILE" | mail -s "SPHERE ETL Failure" admin@example.com
fi
```

---

## Troubleshooting

### El ETL no se ejecuta

1. **Verificar que el script es ejecutable** (Linux/Mac):
   ```bash
   ls -l run_etl_cron.sh
   chmod +x run_etl_cron.sh
   ```

2. **Verificar que Conda está en el PATH**:
   ```bash
   which conda
   echo $PATH
   ```

3. **Ejecutar manualmente y ver errores**:
   ```bash
   ./run_etl_cron.sh
   ```

4. **Verificar permisos de escritura en logs**:
   ```bash
   ls -ld etl/logs
   ```

### Logs vacíos

- Verificar que la redirección de output funciona: `>> $LOGFILE 2>&1`
- Asegurarse de que el directorio `logs/` existe
- Verificar permisos de escritura

### MongoDB no conecta

- Verificar que el archivo `.env` tiene las credenciales correctas
- Verificar conectividad de red

---

## Recomendaciones

✅ **Frecuencia Sugerida**: Ejecución semanal (domingos a las 3:00 AM)

✅ **Retención de Logs**: Mantener logs de los últimos 30 días

✅ **Monitoreo**: Revisar logs semanalmente para detectar errores

✅ **Backup**: Respaldar MongoDB regularmente (independiente del ETL)

✅ **Testing**: Probar la tarea programada manualmente antes de dejarla en automático
