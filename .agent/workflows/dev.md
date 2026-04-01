---
description: Ejecutar el backend SPHERE localmente fuera de Docker
---

# Desarrollo Local del Backend

## Prerrequisitos

1. Asegúrate de tener Python 3.10+ instalado
2. Verifica que existe el archivo `.env` en la raíz del proyecto con:
   - `MONGODB_URL` - URI de conexión a MongoDB Atlas
   - `DEEPSEEK_API_KEY` - API key para el LLM

## Pasos

### 1. Instalar dependencias
```bash
cd backend
pip install -r requirements.txt
```

### 2. Ejecutar backend local
// turbo
```bash
cd backend
python run_local.py
```

### 3. Ejecutar con opciones avanzadas
```bash
# Puerto personalizado
python run_local.py --port 8001

# Logs detallados
python run_local.py --log-level debug

# Auto-reload en desarrollo
python run_local.py --reload
```

### 4. Verificar conexión
// turbo
```bash
curl http://localhost:8000/api/v1/health/health
```

## Ejecutar Tests

// turbo
```bash
cd backend
pytest tests/ -v -s
```

### Solo tests de conexión
```bash
pytest tests/test_connection.py -v
```

### Solo tests de un endpoint específico
```bash
pytest tests/test_sessions.py -v
pytest tests/test_agents.py -v
```
