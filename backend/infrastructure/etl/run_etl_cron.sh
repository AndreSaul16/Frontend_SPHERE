#!/usr/bin/env bash
# ============================================================
# SPHERE ETL - Script de Ejecución Periódica (CRON)
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activar entorno Conda
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate base

# Crear directorio de logs si no existe
mkdir -p logs

# Generar nombre de archivo de log con timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOGFILE="logs/etl_cron_${TIMESTAMP}.log"

{
  echo "================================================"
  echo "SPHERE ETL - Ejecución Automática"
  echo "Fecha: $(date)"
  echo "================================================"
} >> "$LOGFILE"

python run_etl.py --agent cto >> "$LOGFILE" 2>&1
EXITCODE=$?

{
  echo ""
  echo "================================================"
  echo "Ejecución finalizada. Código de salida: $EXITCODE"
  echo "================================================"
} >> "$LOGFILE"

echo "ETL ejecutado. Ver log: $LOGFILE"
exit $EXITCODE
