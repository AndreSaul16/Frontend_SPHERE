# Spiders del CTO

Spiders especializados para el Chief Technology Officer (CTO).

## Spiders Disponibles

### 1. GitHub Governance Spider (`github_spider.py`)

Extrae documentación de gobernanza y arquitectura de repositorios críticos.

**Repositorios objetivo**:
- Kubernetes (`kubernetes/kubernetes`)
- Elasticsearch (`elastic/elasticsearch`)
- PyTorch (`pytorch/pytorch`)
- React (`facebook/react`)
- Linux Kernel (`torvalds/linux`)

**Archivos que busca**:
- `ARCHITECTURE.md`, `CONTRIBUTING.md`, `GOVERNANCE.md`
- Carpetas: `docs/design-proposals/`, `docs/architecture/`

**Datos guardados en**: `data/raw/cto/github/`

### 2. Engineering Blogs Spider (`blogs_spider.py`)

Extrae artículos de blogs de ingeniería con filtrado por keywords.

**Keywords de alto valor**:
- migration, scaling, post-mortem, incident, outage
- architecture, refactoring, performance
- distributed, infrastructure, microservices, database

**Fuentes**:
- **Netflix Tech Blog**: Top 10 artículos sobre microservicios
- **Uber Engineering**: 5 artículos sobre migraciones de DB
- **Discord Engineering**: Artículos sobre escalabilidad de Elixir/ScyllaDB

**Datos guardados en**: `data/raw/cto/blogs/`

### 3. ArXiv Papers Spider (`papers_spider.py`)

Busca papers fundacionales clásicos y recientes sobre LLM Ops.

**Papers objetivo**:
- Google File System
- MapReduce
- Dynamo (Amazon)
- Kafka
- Attention Is All You Need
- BERT

**Papers recientes**: LLM operations, deployment

**Datos guardados en**: `data/raw/cto/papers/`

## Uso

### Ejecutar todos los spiders del CTO

```bash
cd c:\Users\Saul\Documents\PROGRAMACION\SPHERE\etl
python run_etl.py --agent cto
```

### Ejecutar spider específico

```bash
# GitHub
python agents\cto\github_spider.py

# Blogs
python agents\cto\blogs_spider.py

# Papers
python agents\cto\papers_spider.py
```

## Configuración Opcional

### GitHub Token (recomendado)

Agrega a `.env` para aumentar rate limits:

```env
GITHUB_TOKEN=ghp_your_token_here
```

Sin token: 60 requests/hora
Con token: 5,000 requests/hora
