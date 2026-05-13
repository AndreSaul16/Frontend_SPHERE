<p align="center">
  <img src="https://img.shields.io/badge/ETL-Pipeline-10B981?style=for-the-badge&labelColor=0D0D1A&color=10B981" />
  <img src="https://img.shields.io/badge/Spiders-17-7C3AED?style=for-the-badge&labelColor=0D0D1A&color=7C3AED" />
  <img src="https://img.shields.io/badge/Documents-74-3B82F6?style=for-the-badge&labelColor=0D0D1A&color=3B82F6" />
</p>

<h1 align="center">ETL — SPHERE</h1>
<p align="center">
  Pipeline de ingestión de conocimiento que alimenta la base RAG de cada agente<br/>
  con contenido curado de alta calidad: blogs, papers, frameworks, y case studies.
</p>

---

## ¿Qué hace el ETL?

El ETL es el sistema que **alimenta el cerebro** de los agentes. Sin datos, los agentes no tienen contexto. El ETL:

```
┌─────────────────────────────────────────────────────────────────┐
│                        PIPELINE ETL                              │
│                                                                 │
│  1. SCRAPE (Spiders)                                            │
│     Descarga contenido de fuentes curadas (blogs, papers, APIs) │
│                                                                 │
│  2. CLEAN (Procesamiento)                                       │
│     Limpia HTML, extrae texto de PDFs, elimina referencias      │
│                                                                 │
│  3. STORE (MongoDB)                                             │
│     Guarda documentos procesados en la colección knowledge_base │
│                                                                 │
│  4. VECTORIZE (OpenAI)                                          │
│     Genera embeddings de 1536 dimensiones para búsqueda RAG     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Arquitectura Medallion

El ETL sigue un patrón de 3 capas (Medallion Architecture):

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  BRONZE LAYER              SILVER LAYER           GOLD LAYER    │
│  (Archivos crudos)         (MongoDB)              (Embeddings)  │
│                                                                 │
│  data/raw/                 knowledge_base         embedding[]   │
│  ├── cto/                  collection             1536 dims     │
│  │   ├── blogs/            ┌─────────────┐       ┌──────────┐  │
│  │   ├── papers/           │ content_    │       │ OpenAI   │  │
│  │   └── books/            │ markdown    │──────▶│ text-    │  │
│  ├── ceo/                  │             │       │ embedding│  │
│  │   └── mckinsey/         │ metadata    │       │ -3-small │  │
│  ├── cfo/                  │ tags        │       └──────────┘  │
│  │   ├── saas/             │ url         │                     │
│  │   ├── regulatory/       │ agent_target│                     │
│  │   └── macro/            │ user_id     │                     │
│  └── cmo/                  └─────────────┘                     │
│      ├── blogs/                                                │
│      ├── frameworks/        ↑                                  │
│      └── case_studies/      migrate_bronze_to_silver.py        │
│                            (script de migración)               │
│                                                                 │
│  .html .md .pdf            Documentos limpios     Vectores     │
│  sin procesar              con metadata           para RAG     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Spiders por Agente

### CTO (Nexus) — ~31 documentos

| Spider | Fuente | Tipo | Contenido |
|--------|--------|------|-----------|
| `GitHubGovernanceSpider` | GitHub (K8s, React, PyTorch, Elasticsearch, Linux) | API | Docs de arquitectura, governance, contributing |
| `NetflixEngineeringSpider` | Netflix Tech Blog (RSS) | Blog | Migration, scaling, post-mortems |
| `UberEngineeringSpider` | Uber Engineering (RSS) | Blog | Database, postgres, migration |
| `DiscordEngineeringSpider` | Discord Blog (HTML) | Blog | Infrastructure, performance |
| `ArxivFoundationalSpider` | ArXiv API | Papers | Attention Is All You Need, BERT, Raft, GFS, etc. |
| `ArxivPDFSpider` | ArXiv (PDF download) | Papers | Descarga PDFs de papers flaggeados |
| `BooksSyntheticSpider` | data/synthetic/cto/books/ | Libros | Libros sintéticos de DevOps, arquitectura |

### CEO (Oberon) — ~5 documentos

| Spider | Fuente | Tipo | Contenido |
|--------|--------|------|-----------|
| `McKinseySpider` | McKinsey Featured Insights | Blog | Estrategia, liderazgo, transformación digital |

### CFO (Ledger) — ~7 documentos

| Spider | Fuente | Tipo | Contenido |
|--------|--------|------|-----------|
| `DavidSkokSpider` | forentrepreneurs.com | Blog | SaaS metrics (CAC, LTV, churn) |
| `OpenViewSpider` | openviewpartners.com | Blog | Rule of 40, PLG benchmarks |
| `ChartMogulSpider` | chartmogul.com | Blog | NDR, cohort analysis |
| `AnnualReportsSpider` | Berkshire Hathaway (PDF) | Regulatory | 10-K, annual report |
| `AccountingStandardsSpider` | FASB | Regulatory | ASC 606 revenue recognition |
| `BoardDeckSpider` | Sequoia Capital | Regulatory | Board deck template |
| `HowardMarksSpider` | Oaktree Capital | Macro | Investment memos |
| `DamodaranSpider` | NYU Stern | Macro | Equity risk premium |
| `SequoiaSpider` | Sequoia Capital | Macro | Crisis memos |
| `RayDalioSpider` | Bridgewater | Macro | Economic machine, debt crises |

### CMO (Vortex) — ~31 documentos

| Spider | Fuente | Tipo | Contenido |
|--------|--------|------|-----------|
| `ReforgeSpider` | Reforge (RSS) | Blog | Growth loops, product strategy |
| `AndrewChenSpider` | a16z (RSS) | Blog | Network effects, virality |
| `MozBlogSpider` | Moz (RSS) | Blog | Technical SEO |
| `AhrefsBlogSpider` | Ahrefs (RSS) | Blog | Data-driven SEO |
| `KellblogSpider` | Dave Kellogg (RSS) | Blog | SaaS metrics |
| `MarketingFrameworkSpider` | PDFs (Binet & Field, Google, etc.) | Framework | Long & Short of It, Messy Middle |
| `WebFrameworkSpider` | Web pages | Framework | See-Think-Do-Care, 1000 True Fans |
| `CaseStudySpider` | Curated URLs | Case Study | Airbnb, Dropbox, Salesforce, HubSpot, etc. |

---

## Clase Base — BaseTechSpider

Todos los spiders heredan de `BaseTechSpider` (Template Method Pattern):

```python
class BaseTechSpider(ABC):
    def __init__(self, agent_name: str):
        # Conecta a MongoDB Atlas
        # Configura headers realistas

    def url_exists(url: str) -> bool:
        # Deduplicación: ¿ya existe este URL?

    def save_knowledge(data: dict):
        # Upsert a MongoDB (idempotent)

    def extract_content(url: str) -> str:
        # Descarga HTML → extrae markdown limpio con trafilatura

    def save_raw_html(url, title, agent_subdir):
        # Guarda archivo crudo (Bronze Layer)

    @abstractmethod
    def run(self):
        # Cada spider implementa su lógica
```

### Jerarquía de herencia

```
BaseTechSpider (ABC)
├── CuratedBlogSpider (+ HIGH_VALUE_KEYWORDS filter)
│   ├── NetflixEngineeringSpider
│   ├── UberEngineeringSpider
│   └── DiscordEngineeringSpider
│
├── CuratedMarketingBlogSpider (+ keywords + anti-patterns)
│   ├── ReforgeSpider
│   ├── AndrewChenSpider
│   ├── MozBlogSpider
│   ├── AhrefsBlogSpider
│   └── KellblogSpider
│
├── SaaSMetricsSpider (+ FINANCE_KEYWORDS)
│   ├── DavidSkokSpider
│   ├── OpenViewSpider
│   └── ChartMogulSpider
│
├── RegulatorySpider (+ PDF extraction)
│   ├── AnnualReportsSpider
│   ├── AccountingStandardsSpider
│   └── BoardDeckSpider
│
├── MacroSpider (+ MACRO_KEYWORDS)
│   ├── HowardMarksSpider
│   ├── DamodaranSpider
│   ├── SequoiaSpider
│   └── RayDalioSpider
│
├── GitHubGovernanceSpider
├── ArxivFoundationalSpider
├── ArxivPDFSpider
├── BooksSyntheticSpider
├── McKinseySpider
├── MarketingFrameworkSpider (+ PDF extraction)
├── WebFrameworkSpider
└── CaseStudySpider (+ PDF + metrics extraction)
```

---

## Scripts de procesamiento

| Script | Propósito | Cuándo usarlo |
|--------|-----------|---------------|
| `run_etl.py` | CLI principal — ejecuta spiders por agente | Ejecución regular |
| `scripts/migrate_bronze_to_silver.py` | Migra archivos crudos a MongoDB sin re-descargar | Después de agregar archivos manualmente |
| `scripts/process_synthetic_books.py` | Procesa libros sintéticos CTO (limpia referencias) | Después de generar libros |
| `scripts/process_new_synthetic_pdfs.py` | Procesa PDFs sintéticos nuevos (CEO, CFO, CMO) | Después de generar PDFs |
| `scripts/vectorize_corpus.py` | Genera embeddings para documentos sin vectorizar | Después de agregar documentos |
| `scripts/url_validator.py` | Pre-valida URLs antes de ejecutar spiders | Antes de ejecutar ETL |
| `scripts/check_data.py` | Analiza distribución de datos en MongoDB | Para verificar estado |
| `scripts/analyze_db.py` | Stats rápidas de MongoDB (por source, agent_target) | Para verificar estado |

---

## Comandos

### Ejecución principal

```bash
# Ejecutar TODOS los spiders de un agente
python run_etl.py --agent cto
python run_etl.py --agent ceo
python run_etl.py --agent cfo    # (usa orquestador propio)
python run_etl.py --agent cmo    # (usa orquestador propio)
python run_etl.py --agent all

# Ejecutar un spider específico
python run_etl.py --spider github
python run_etl.py --spider netflix
python run_etl.py --spider arxiv
python run_etl.py --spider mckinsey
```

### Orquestadores por agente

```bash
# CFO — ejecuta las 3 fases (SaaS, Regulatory, Macro)
python -m etl.agents.cfo --limit 5
python -m etl.agents.cfo --quick    # 1 doc por spider

# CMO — ejecuta las 3 fases (Blogs, Frameworks, Case Studies)
python -m etl.agents.cmo --blogs 5 --frameworks 3 --case-studies 2
python -m etl.agents.cmo --quick
```

### Scripts de procesamiento

```bash
# Migrar Bronze → Silver (sin re-descargar)
python etl/scripts/migrate_bronze_to_silver.py

# Procesar libros sintéticos
python etl/scripts/process_synthetic_books.py

# Procesar PDFs sintéticos nuevos
python etl/scripts/process_new_synthetic_pdfs.py

# Vectorizar documentos nuevos
python etl/scripts/vectorize_corpus.py

# Validar URLs antes de ejecutar
python etl/scripts/url_validator.py --corpus docs/corpus.md

# Verificar estado de la DB
python etl/scripts/analyze_db.py
```

---

## Calidad sobre cantidad

**SPHERE NO hace mass scraping.** Cada spider tiene filtros de keywords que seleccionan solo contenido de alta valor:

```
Netflix Engineering Blog:
  ✅ "migration", "scaling", "post-mortem", "architecture"
  ❌ "top 10", "for beginners", "get rich quick"

ArXiv Papers:
  ✅ Papers fundacionales específicos (Attention Is All You Need, BERT, Raft)
  ❌ Búsqueda genérica de papers

Frameworks:
  ✅ Binet & Field "The Long and the Short of It"
  ✅ Google "The Messy Middle"
  ❌ Cualquier artículo de marketing
```

**Resultado: ~74 documentos curados** de altísima calidad, no miles de documentos ruidosos.

---

## Diseño de datos — Schema v2.0

Cada documento en MongoDB tiene esta estructura:

```json
{
  "_id": "ObjectId",
  "url": "https://netflix.com/techblog/post-123",
  "title": "How Netflix Scaled to 100M Users",
  "source": "netflix_engineering",
  "agent_target": "CTO",
  "content_markdown": "# How Netflix...\n\nFull article text...",
  "content_type": "markdown",
  "tags": ["scaling", "netflix", "microservices"],
  "ingested_at": "2026-03-15T10:30:00Z",
  "needs_pdf_processing": false,
  "embedding": [0.0012, -0.0034, ...],  // 1536 dims (Gold Layer)
  "metadata": {
    "word_count": 2500,
    "references_removed": 0
  }
}
```

### Campos clave

| Campo | Propósito |
|-------|-----------|
| `url` | Deduplicación (upsert key) |
| `agent_target` | Qué agente usa este documento (CTO, CEO, CFO, CMO, custom_id, "all") |
| `content_markdown` | Texto limpio procesado |
| `embedding` | Vector de 1536 dimensiones para RAG |
| `tags` | Para filtrado y organización |
| `needs_pdf_processing` | Flag para el spider de PDFs (dos fases) |

---

## Documentación adicional

| Documento | Contenido |
|-----------|-----------|
| [Resumen_ETL.md](Resumen_ETL.md) | Diario completo de 7 días de desarrollo (1017 líneas) |
| [README_CRON.md](README_CRON.md) | Guía de automatización con cron/Task Scheduler |
| [etl/agents/cto/README.md](agents/cto/README.md) | Documentación específica del CTO |
| [etl/agents/ceo/README.md](agents/ceo/README.md) | Documentación específica del CEO |
