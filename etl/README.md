# 📡 SPHERE ETL - Sistema de Vigilancia Tecnológica

Sistema automatizado de extracción, transformación y carga (ETL) de conocimiento técnico desde múltiples fuentes especializadas, organizado por agentes ejecutivos.

## 🏗️ Arquitectura

```
etl/
├── core/                          # Código compartido
│   ├── base_spider.py            # Clase base BaseTechSpider
│   └── __init__.py
│
├── agents/                        # Spiders organizados por agente
│   ├── cto/                      # Chief Technology Officer
│   │   ├── github_spider.py      # GitHub Governance
│   │   ├── blogs_spider.py       # Netflix, Uber, Discord
│   │   ├── papers_spider.py      # ArXiv Foundational
│   │   └── README.md
│   │
│   ├── ceo/                      # Chief Executive Officer
│   │   ├── mckinsey_spider.py    # McKinsey Insights
│   │   └── README.md
│   │
│   ├── cfo/                      # Chief Financial Officer (futuro)
│   └── cmo/                      # Chief Marketing Officer (futuro)
│
├── scripts/                       # Utilidades
│   └── check_data.py             # Verificar datos en MongoDB
│
├── run_etl.py                    # 🎯 Orquestador principal
├── requirements.txt              # Dependencias
└── README.md                     # Este archivo
```

## 🗄️ Organización de Datos

```
data/raw/
├── cto/                          # Datos del CTO
│   ├── github/                   # Archivos de gobernanza de GitHub
│   ├── blogs/                    # Artículos de blogs de ingeniería
│   └── papers/                   # Papers de ArXiv (si se descargan PDFs)
│
├── ceo/                          # Datos del CEO
│   └── McKinsey_*.html
│
├── cfo/                          # Datos del CFO (futuro)
└── cmo/                          # Datos del CMO (futuro)
```

## 🚀 Uso Rápido

### Ejecutar todos los spiders

```bash
python run_etl.py --agent all
```

### Ejecutar spiders por agente

```bash
python run_etl.py --agent cto    # Solo CTO
python run_etl.py --agent ceo    # Solo CEO
```

### Ejecutar spider específico

```bash
python run_etl.py --spider github     # GitHub Governance
python run_etl.py --spider netflix    # Netflix Blog
python run_etl.py --spider mckinsey   # McKinsey
```

### Verificar datos ingresados

```bash
python scripts\check_data.py
```

## 📚 Spiders Disponibles

### CTO (Chief Technology Officer)

| Spider | Fuente | Output Esperado | Ubicación |
|--------|--------|-----------------|-----------|
| **GitHub Governance** | Kubernetes, Elasticsearch, PyTorch, React, Linux | ~50 docs | `data/raw/cto/github/` |
| **Engineering Blogs** | Netflix, Uber, Discord | ~75 artículos | `data/raw/cto/blogs/` |
| **ArXiv Papers** | Papers fundacionales + LLM Ops | ~20 papers | MongoDB (abstracts) |

**Total**: ~145 documentos de alta densidad técnica

### CEO (Chief Executive Officer)

| Spider | Fuente | Output Esperado | Ubicación |
|--------|--------|-----------------|-----------|
| **McKinsey** | McKinsey Featured Insights | ~10-20 artículos | `data/raw/ceo/` |

## 🔧 Configuración

### Variables de Entorno Requeridas

Archivo `.env` en la raíz del proyecto:

```env
# MongoDB (Requerido)
MONGODB_URL=mongodb+srv://usuario:password@cluster.mongodb.net/
DB_NAME=sphere_db

# GitHub Token (Opcional pero recomendado)
GITHUB_TOKEN=ghp_your_token_here
```

### Instalación de Dependencias

```bash
pip install -r requirements.txt
```

Dependencias principales:
- `pymongo` - Cliente MongoDB
- `trafilatura` - Extracción de contenido web
- `beautifulsoup4` - Parsing HTML
- `feedparser` - Lectura de RSS feeds
- `lxml` - Parsing XML para ArXiv
- `python-dotenv` - Variables de entorno

## 📖 Documentación Detallada

- [Spiders del CTO](./agents/cto/README.md) - GitHub, Blogs, Papers
- [Spiders del CEO](./agents/ceo/README.md) - McKinsey
- [CURATED_SPIDERS.md](./CURATED_SPIDERS.md) - Filosofía del sistema curado

## 🎯 Filosofía: Calidad sobre Cantidad

Este sistema NO hace scraping masivo. Cada spider está **finamente ajustado** para extraer solo contenido de alto valor:

- ✅ ~100-150 documentos de altísima densidad técnica
- ✅ Filtrado por keywords específicas
- ✅ Listas curadas manualmente de repositorios y fuentes
- ✅ Detección automática de duplicados
- ❌ No descarga código fuente ni archivos irrelevantes

## 🔄 Ejecución Automática (CRON)

### Linux/Mac

```bash
# Ejecutar cada domingo a las 6 AM
0 6 * * 0 cd /ruta/SPHERE/etl && python run_etl.py --agent all
```

### Windows (Task Scheduler)

```powershell
schtasks /create /sc weekly /d SUN /tn "SPHERE_ETL" /tr "python run_etl.py --agent all" /st 06:00
```

## 🛠️ Cómo Agregar un Nuevo Agente

### Ejemplo: CFO Spider

1. **Crear carpeta del agente**:
```bash
mkdir agents\cfo
New-Item agents\cfo\__init__.py
```

2. **Crear spider específico** (`agents/cfo/bloomberg_spider.py`):
```python
from core.base_spider import BaseTechSpider

class BloombergSpider(BaseTechSpider):
    def __init__(self):
        super().__init__(agent_name="CFO")
    
    def run(self, limit=10):
        # Implementar lógica específica
        pass
```

3. **Actualizar orquestador** (`run_etl.py`):
```python
from agents.cfo.bloomberg_spider import BloombergSpider

def run_cfo_spiders():
    bloomberg_spider = BloombergSpider()
    bloomberg_spider.run()
```

4. **Crear subcarpeta de datos**:
```bash
mkdir data\raw\cfo
```

## 📊 Ventajas de Esta Arquitectura

### ✅ Escalabilidad
- Agregar nuevos agentes es crear una carpeta en `agents/`
- Datos automáticamente organizados por agente

### ✅ Mantenibilidad
- Código compartido en `core/`
- Un cambio en MongoDB afecta a todos los spiders automáticamente

### ✅ Claridad
```python
from core.base_spider import BaseTechSpider  # Claro
from agents.cto.github_spider import GitHubGovernanceSpider  # Claro
```

### ✅ Aislamiento de Fallos
- Si un spider falla, los demás continúan
- Cada agente puede ejecutarse independientemente

## ⚠️ Rate Limits y Buenas Prácticas

| Fuente | Sin Token | Con Token | Delay |
|--------|-----------|-----------|-------|
| GitHub API | 60 req/hora | 5,000 req/hora | 1s |
| Blogs (RSS) | N/A | N/A | 2-3s |
| ArXiv API | N/A | N/A | 2s |
| McKinsey | N/A | N/A | 3s |

## 🐛 Troubleshooting

### Error: "No module named 'core'"

Ejecuta desde la raíz de `etl/`:
```bash
cd c:\Users\Saul\Documents\PROGRAMACION\SPHERE\etl
python run_etl.py
```

### Error: "MONGODB_URL is not defined"

Verifica que el archivo `.env` existe en la raíz del proyecto y contiene:
```env
MONGODB_URL=mongodb+srv://...
DB_NAME=sphere_db
```

### GitHub Rate Limit

Agrega un token de GitHub al `.env`:
```env
GITHUB_TOKEN=ghp_your_token_here
```

## 📝 Changelog

### v2.0 - Reorganización por Agentes (2026-01-12)
- ✅ Reorganizada estructura en `core/` y `agents/`
- ✅ Separados datos por agente en `data/raw/`
- ✅ Creado orquestador `run_etl.py`
- ✅ Spiders del CTO: GitHub, Blogs, Papers
- ✅ Spider del CEO: McKinsey
- ✅ Movidas utilidades a `scripts/`

### v1.0 - Sistema Curado Inicial
- Implementación inicial con `curated_spiders.py`
- Clase base `BaseTechSpider`
- Filtrado por keywords

## 📧 Soporte

Para dudas o mejoras, consulta los READMEs específicos de cada agente:
- [CTO README](./agents/cto/README.md)
- [CEO README](./agents/ceo/README.md)
