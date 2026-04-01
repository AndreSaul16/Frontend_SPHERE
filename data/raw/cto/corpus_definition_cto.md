# 📂 Diseño del Corpus de Conocimiento - CTO (Chief Technology Officer)

**ID del Documento**: `SPHERE-DATA-CTO-002`  
**Responsable**: Saúl Briceño (Data Engineer)  
**Estado**: 🟢 Listo para Ingesta

---

## 1. Visión y Estrategia

### El Objetivo "Golden Standard"

Construir el cerebro de un CTO que ha vivido la evolución desde el monolito hasta los microservicios, y desde el *on-premise* hasta el *serverless*. No queremos un agente que recite manuales, sino uno que entienda el **dolor** de las malas decisiones arquitectónicas.

### Filosofía del Corpus

**"Densidad sobre Volumen"**: Preferimos 300 documentos curados de máxima densidad técnica que 10,000 artículos genéricos.

**Principios**:
- ✅ Solo fuentes de primer nivel (empresas tech líderes, papers citados > 1000 veces)
- ✅ Contenido evergreen (relevante en 5+ años)
- ✅ Foco en decisiones y post-mortems, no tutoriales
- ✅ Filtrado dual: keywords positivas + anti-patrones
- ❌ Bloqueo automático de contenido superficial

---

## 2. Arquitectura de Datos (Pipeline Polimórfico)

Implementamos una arquitectura Medallion estricta para garantizar trazabilidad:

### 🟤 BRONZE (Landing Zone)
- **Formato**: Original (`.html`, `.pdf`, `.md`)
- **Almacenamiento**: File System (`data/raw/<agent>/`)
- **Propósito**: Auditoría y recuperación ante fallos de parseo
- **Retención**: Indefinida (backups inmutables)

### ⚪ SILVER (Knowledge Base)
- **Formato**: Markdown Limpio + Metadata Enriquecida
- **Almacenamiento**: MongoDB Atlas (`collection: knowledge_base`)
- **Propósito**: Fuente para RAG y búsquedas semánticas
- **Schema**:
```json
{
  "source": "Netflix Tech Blog",
  "title": "...",
  "url": "...",
  "file_path": "data/raw/cto/blogs/netflix_article.html",
  "content_markdown": "# Title\n\nContent...",
  "tags": ["architecture", "scaling"],
  "agent_target": "CTO",
  "curated_category": "engineering_blog",
  "ingested_at": "2026-01-13",
  "word_count": 3500,
  "metadata": {
    "author": "...",
    "published_date": "...",
    "complexity_score": 0.85
  }
}
```

### 🟡 GOLD (Training Set)
- **Formato**: Pares JSONL `{"instruction": "...", "response": "..."}`
- **Almacenamiento**: Hugging Face / S3
- **Propósito**: Fine-Tuning (QLoRA) del modelo final
- **Nota**: Fase 3-4 (futuro)

---

## 3. Inventario Maestro de Fuentes (Con URLs Directas)

> **⚠️ Instrucción de Implementación**: Estas URLs están listas para copiar a `config/sources_cto.json` o directamente a los spiders.

### A. GitHub Governance & Design (7 docs → 50 objetivo)

**Foco**: Estándares de facto en la industria, gobernanza de proyectos a escala masiva.

#### Archivos de Gobernanza (Raíz)

| Proyecto | Archivo | URL Raw (Ingesta Directa) | Por Qué Es Vital |
|----------|---------|---------------------------|------------------|
| **Kubernetes** | `GOVERNANCE.md` | `https://raw.githubusercontent.com/kubernetes/community/master/governance.md` | El estándar de orquestación global |
| **Kubernetes** | `VISION.md` | `https://raw.githubusercontent.com/kubernetes/community/master/sig-architecture/charter.md` | Cómo escalar decisiones técnicas |
| **Linux** | `CODE_OF_CONDUCT` | `https://raw.githubusercontent.com/torvalds/linux/master/Documentation/process/code-of-conduct.rst` | Gestión de comunidades masivas |
| **React** | `CODEBASE_OVERVIEW` | `https://raw.githubusercontent.com/facebook/react/main/packages/react/README.md` | Arquitectura de frontend a escala |
| **PyTorch** | `CONTRIBUTING.md` | `https://raw.githubusercontent.com/pytorch/pytorch/main/CONTRIBUTING.md` | Ingeniería de ML a gran escala |
| **Elasticsearch** | `CONTRIBUTING.md` | `https://raw.githubusercontent.com/elastic/elasticsearch/main/CONTRIBUTING.md` | Sistemas distribuidos y estado |

#### Design Proposals & Architecture Docs

| Proyecto | Carpeta Target | Ejemplo de Contenido | Docs Objetivo |
|----------|----------------|----------------------|---------------|
| **Kubernetes** | `/docs/design-proposals/` | KEPs (Kubernetes Enhancement Proposals) | 15 |
| **Elasticsearch** | `/docs/reference/` | Distributed architecture decisions | 10 |
| **PyTorch** | `/docs/source/notes/` | Neural network engineering patterns | 12 |
| **React** | `/packages/react-reconciler/` | Fiber architecture internals | 8 |
| **Linux** | `/Documentation/process/` | Kernel development workflows | 5 |

**Total GitHub Objetivo**: **50 documentos**

---

### B. Engineering Blogs (5 docs → 175 objetivo)

**Foco**: "War Stories", Post-Mortems, Architecture at Scale. Usamos RSS para evitar selectores CSS frágiles.

#### Blogs Implementados (Fase 1)

| Empresa | Enfoque Principal | URL del Feed RSS/Atom | Dificultad | Docs Objetivo |
|---------|-------------------|------------------------|------------|---------------|
| **Netflix Tech** | Chaos Eng, Microservices | `https://netflixtechblog.com/feed`<br>`https://medium.com/feed/netflix-techblog` | 🟡 Media | 30 |
| **Uber Eng** | High Scale, Big Data | `https://www.uber.com/blog/engineering/rss/` | 🟢 Baja | 20 |
| **Discord Eng** | Real-time, Elixir, Rust | `https://discord.com/blog/rss` | 🔴 Alta | 15 |

#### Blogs Pendientes (Fase 1b - Alta Prioridad)

| Empresa | Enfoque | URL del Feed | Dificultad | Docs Objetivo |
|---------|---------|--------------|------------|---------------|
| **Airbnb Eng** | Service Oriented Arch | `https://medium.com/feed/airbnb-engineering` | 🟡 Media | 25 |
| **AWS Architecture** | Cloud Patterns, Reliability | `https://aws.amazon.com/blogs/architecture/feed/` | 🟢 Baja | 30 |
| **GitHub Eng** | DevTools, Database | `https://github.blog/category/engineering/feed/` | 🟢 Baja | 20 |
| **LinkedIn Eng** | Data Infrastructure | `https://engineering.linkedin.com/blog.rss` | 🟡 Media | 20 |
| **Dropbox Tech** | Storage, Python at Scale | `https://dropbox.tech/feed` | 🟢 Baja | 10 |

**Total Blogs Objetivo**: **160 documentos**

---

### C. Academic Papers (7 docs → 30 objetivo)

#### Foundational Papers (2 docs → 12 objetivo)

**Foco**: Los documentos que cambiaron la historia. Ingesta vía procesamiento PDF completo.

| Título | Año | Citas | Temática | URL Directa al PDF (Estable) |
|--------|-----|-------|----------|------------------------------|
| **Google File System** | 2003 | 5000+ | Distributed Storage | `https://research.google.com/archive/gfs-sosp2003.pdf` |
| **MapReduce** | 2004 | 10000+ | Parallel Processing | `https://research.google.com/archive/mapreduce-osdi04.pdf` |
| **Bigtable** | 2006 | 3000+ | NoSQL / Columnar DB | `https://research.google.com/archive/bigtable-osdi06.pdf` |
| **Dynamo (Amazon)** | 2007 | 4000+ | High Availability / CAP | `https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf` |
| **Spanner** | 2012 | 1000+ | Global Consistency | `https://www.usenix.org/system/files/conference/osdi12/osdi12-final-16.pdf` |
| **Raft Algorithm** | 2014 | 2000+ | Distributed Consensus | `https://raft.github.io/raft.pdf` |
| **Chubby** | 2006 | 1500+ | Distributed Locking | `https://research.google.com/archive/chubby-osdi06.pdf` |
| **Kafka** | 2011 | 2500+ | Event Streaming | `https://notes.stephenholiday.com/Kafka.pdf` |
| **Cassandra** | 2010 | 2000+ | Wide-column NoSQL | `https://www.cs.cornell.edu/projects/ladis2009/papers/lakshman-ladis2009.pdf` |
| **TAO (Facebook)** | 2013 | 800+ | Graph Data at Scale | `https://www.usenix.org/system/files/conference/atc13/atc13-bronson.pdf` |
| **Attention Is All You Need** | 2017 | 50000+ | Transformers | `https://arxiv.org/pdf/1706.03762.pdf` |
| **BERT** | 2018 | 30000+ | NLP Pre-training | `https://arxiv.org/pdf/1810.04805.pdf` |

**Stack para Procesamiento PDF** (Fase 2):
```python
import PyPDF2
import pdfplumber  # Mejor extracción que PyPDF2

def extract_pdf_from_url(url):
    response = requests.get(url, verify=False)
    pdf = pdfplumber.open(io.BytesIO(response.content))
    
    text = ""
    for page in pdf.pages:
        text += page.extract_text()
    
    return text
```

---

#### Recent Research - LLM Ops & MLOps (5 docs → 18 objetivo)

**Query ArXiv Optimizado**:
```python
arxiv_queries = [
    "LLM operations deployment production",
    "large language model serving inference optimization",
    "MLOps machine learning operations at scale",
    "model monitoring drift detection production",
    "distributed training GPU cluster optimization"
]

# Filtrar: últimos 18 meses, ordenar por citas
```

**Temas Prioritarios**:
- LLM serving (vLLM, TensorRT-LLM, Ray Serve)
- Prompt engineering & caching
- Model versioning & A/B testing
- GPU cost optimization
- ML observability en producción

**Total Papers Objetivo**: **30 documentos**

---

### D. Libros Sintéticos (0 docs → 7 objetivo)

**Foco**: Destilación de modelos mentales complejos. (Ya creados con Deep Research en tu local).

| Libro | Tamaño | Estado | Valor | Ruta Local |
|-------|--------|--------|-------|------------|
| **SRE de Google: Frameworks para IA** | 27 KB | ⚠️ Requiere limpieza | ⭐⭐⭐⭐⭐ | `data/synthetic/cto/books/` |
| **Team Topologies para IA** | - | ⚠️ Requiere limpieza | ⭐⭐⭐⭐⭐ | `data/synthetic/cto/books/` |
| **Accelerate & DORA Metrics** | - | ⚠️ Requiere limpieza | ⭐⭐⭐⭐⭐ | `data/synthetic/cto/books/` |
| **Staff Engineer: IA y Estrategia** | - | ⚠️ Requiere limpieza | ⭐⭐⭐⭐ | `data/synthetic/cto/books/` |
| **Microservicios: Síntesis** | - | ⚠️ Requiere limpieza | ⭐⭐⭐⭐ | `data/synthetic/cto/books/` |
| **Arquitectura de Datos** | - | ⚠️ Requiere limpieza | ⭐⭐⭐⭐ | `data/synthetic/cto/books/` |
| **Ingeniería de Sistemas y Gestión IA** | - | ⚠️ Requiere limpieza | ⭐⭐⭐⭐ | `data/synthetic/cto/books/` |

**Acción Requerida**: 
```bash
python scripts/process_synthetic_books.py
```

**Total Libros Objetivo**: **7 documentos**

---

## 4. Especificación de Filtrado (Quality Gates)

Para asegurar la calidad ("Oro sobre Paja"), el pipeline aplicará filtros estrictos:

### Filtros de Palabras Clave (Positivos)

**Solo ingerir si el contenido menciona al menos 2 de estas**:

```python
KEYWORDS_QUALITY = [
    # Resiliencia & Operaciones
    'post-mortem', 'postmortem', 'incident report', 'root cause analysis',
    'outage', 'downtime', 'reliability', 'availability',
    
    # Deuda Técnica & Refactoring
    'migration', 'refactoring', 'legacy code', 'technical debt',
    'modernization', 'rewrite',
    
    # Performance & Escalabilidad
    'architecture', 'scalability', 'scale', 'latency', 'throughput',
    'performance', 'optimization', 'bottleneck',
    
    # Sistemas Distribuidos
    'consistency', 'availability', 'partition tolerance', 'CAP theorem',
    'consensus', 'replication', 'sharding', 'distributed',
    
    # Infraestructura
    'kubernetes', 'microservices', 'observability', 'monitoring',
    'deployment', 'infrastructure', 'database', 'cache', 'cdn'
]
```

---

### Filtros de Exclusión (Anti-Patrones)

**Descartar inmediatamente si detecta**:

```python
KEYWORDS_BLOCK = [
    # Contenido Superficial
    'top 10', 'top 5', 'best tools', 'best practices for beginners',
    'tutorial for beginners', 'introduction to', 'getting started with',
    'how to install', 'step by step guide',
    
    # Ruido HR/Corporate
    'career advice', 'salary negotiation', 'interview questions',
    'press release', 'quarterly results', 'we are hiring',
    'new office', 'company culture',
    
    # Contenido No-Técnico
    'motivational', 'productivity tips', 'work-life balance',
    'team building', 'soft skills'
]
```

---

### Validación de Longitud Mínima

```python
MIN_WORD_COUNT = 500  # Excepción: manifiestos y governance docs

def validate_document(doc):
    word_count = len(doc['content_markdown'].split())
    
    # Excepciones
    if any(tag in doc.get('tags', []) for tag in ['manifest', 'governance', 'code-of-conduct']):
        return word_count >= 100
    
    return word_count >= MIN_WORD_COUNT
```

---

## 5. Métricas y KPIs de Éxito

### Estado Actual vs. Objetivo Final

| Categoría | Docs Actuales | Docs Objetivo | % Completado | Estado |
|-----------|---------------|---------------|--------------|--------|
| **GitHub Governance** | 7 | 50 | 14% | 🟡 En progreso |
| **Engineering Blogs** | 5 | 175 | 3% | 🟡 En progreso |
| **Foundational Papers** | 2 | 12 | 17% | 🔴 Pendiente PDF |
| **Recent Research** | 5 | 18 | 28% | 🟢 On track |
| **Synthetic Books** | 0 | 7 | 0% | 🔴 Pendiente limpieza |
| **TOTAL** | **19** | **247** | **8%** | 🟡 **Fase 1 inicial** |

---

### KPIs de Fase 2 (Primer Hito)

Sabremos que hemos completado la **Fase 2** cuando:

- [ ] **Total Documentos**: ≥ 150
- [ ] **Papers Fundacionales**: 12/12 procesados con éxito (texto completo de PDFs)
- [ ] **Cobertura de Blogs**: Al menos 1 post-mortem de cada Big Tech listada
- [ ] **Calidad Semántica**: Ningún documento < 500 palabras (excepto manifiestos)
- [ ] **Diversidad Temática**: Cada tema del corpus con ≥ 10 documentos
- [ ] **Bronze Layer**: 100% de documentos tienen backup en disco

---

### Distribución por Tipo de Conocimiento

**Objetivo Final (247 docs)**:

```
Conocimiento Fundacional (Papers + Libros): 37 docs (14%)
├─ Papers clásicos: 12
├─ Papers recientes: 18
└─ Libros sintéticos: 7

Conocimiento Práctico (Blogs): 160 docs (65%)
├─ Netflix, Uber, Discord: 65
├─ Airbnb, AWS, GitHub: 70
└─ LinkedIn, Dropbox: 30

Conocimiento de Gobernanza (GitHub): 50 docs (19%)
├─ ARCHITECTURE/GOVERNANCE/CONTRIBUTING: 15
└─ Design proposals & RFCs: 35
```

**Cobertura Temática Esperada**:
- ✅ Distributed Systems (25%)
- ✅ Architecture & Design Patterns (20%)
- ✅ SRE & Operations (15%)
- ✅ Database Systems (10%)
- ✅ ML/AI Operations (10%)
- ✅ Team & Process (10%)
- ✅ Security & Compliance (5%)
- ✅ Emerging Tech (5%)

---

## 6. Roadmap de Implementación

### Fase 1: Foundation (Semanas 1-2) - Objetivo: 50 docs

**Estado Actual**: 🟡 38% completado (19/50 docs)

- [x] GitHub spider base (7 docs) ✅
- [x] Netflix blog spider (5 docs) ✅
- [x] ArXiv recent papers (5 docs) ✅
- [x] ArXiv foundational (2 docs - solo abstracts) ✅
- [ ] **Pendiente**:
  - [ ] Limpiar libros sintéticos (+7 docs)
  - [ ] Agregar 3 blogs (Airbnb, AWS, GitHub) - (+24 docs estimados)

**Entregables**:
- Sistema operativo y escalable
- 50 documentos de alta calidad en MongoDB
- Bronze layer con backups
- Scripts de validación funcionando

---

### Fase 2: Scale-Up (Semanas 3-4) - Objetivo: +100 docs (150 total)

- [ ] **Procesar PDFs de papers fundacionales** (+10 docs)
  - Implementar `extract_pdf_from_url()` con pdfplumber
  - Procesar lista completa de 12 papers
  
- [ ] **Expandir GitHub a 15 archivos/carpeta** (+43 docs)
  - Modificar límite de 5 → 15
  - Agregar filtro por fecha (últimos 2 años)
  
- [ ] **Agregar 4 blogs adicionales** (+60 docs)
  - Stripe, LinkedIn, Dropbox, Google Cloud Platform
  - Usar configuración de filtros duales
  
- [ ] **ArXiv: ampliar ventana temporal** (+11 docs)
  - De 12 meses → 24 meses
  - Agregar queries adicionales (MLOps, LLMOps)

**Entregables**:
- 150 documentos curados
- Todos los papers fundacionales completos
- Sistema de filtrado dual operativo

---

### Fase 3: Diversification (Mes 2) - Objetivo: +50 docs (200 total)

- [ ] **Libros técnicos completos** (+20 docs)
  - Designing Data-Intensive Applications (caps seleccionados)
  - SRE O'Reilly Book (caps públicos)
  - Building Microservices 2nd Ed.
  
- [ ] **Web scraping avanzado** (+30 docs)
  - Martin Fowler Blog (BeautifulSoup)
  - High Scalability case studies
  - The Morning Paper summaries

**Entregables**:
- 200 documentos
- Cobertura completa de temas core
- Script de web scraping genérico

---

### Fase 4: Production-Ready (Mes 3) - Objetivo: +47 docs (247 total)

- [ ] **Conference talks** (+40 docs)
  - QCon, Strange Loop, GOTO
  - Transcripciones automáticas (Whisper)
  
- [ ] **Re-crawl de blogs** (+22 docs)
  - Contenido nuevo desde Fase 1
  - Blogs sin artículos en primera pasada (Uber, Discord)

- [ ] **Validación y deduplicación final**
- [ ] **Automatización CRON**
- [ ] **Documentación completa**

**Entregables**:
- 247 documentos (100% objetivo)
- Sistema automatizado semanal
- Dashboard de métricas
- Corpus production-ready

---

## 7. Mantenimiento y Actualización

### Estrategia de Freshness

**Frecuencia de Actualización**:

| Fuente | Frecuencia | Método | CRON |
|--------|-----------|--------|------|
| **Engineering Blogs** | Semanal | Automático | `0 6 * * 0` (Dom 6 AM) |
| **ArXiv Papers** | Mensual | Automático | `0 6 1 * *` (1er día mes) |
| **GitHub** | Trimestral | Semi-automático | `0 6 1 */3 *` (Cada 3 meses) |
| **Conference Talks** | Post-evento | Manual | - |

**CRON Configuration (Windows Task Scheduler)**:
```powershell
# Blogs: Cada domingo 6 AM
schtasks /create /sc weekly /d SUN /tn "SPHERE_ETL_Blogs" ^
  /tr "python run_etl.py --sources blogs" /st 06:00

# Papers: Primer día de cada mes
schtasks /create /sc monthly /d 1 /tn "SPHERE_ETL_Papers" ^
  /tr "python run_etl.py --sources papers" /st 06:00
```

---

## 8. Gobernanza y Calidad

### Validación de Entrada

```python
def validate_document_quality(doc):
    """
    Quality gates para aceptación automática.
    """
    checks = {
        'min_length': len(doc.content.split()) >= 500,
        'no_marketing': not contains_blocked_keywords(doc),
        'has_quality_keywords': count_quality_keywords(doc) >= 2,
        'technical_density': calculate_technical_ratio(doc) >= 0.15,
        'readability': flesch_reading_ease(doc) < 40,  # Universitario+
        'has_code_or_diagrams': has_technical_content(doc)
    }
    
    # Log de rechazo para análisis
    if not all(checks.values()):
        rejected_reasons = [k for k, v in checks.items() if not v]
        log_rejection(doc.url, rejected_reasons)
    
    return all(checks.values())
```

### Detección de Duplicados

**Niveles de Detección**:
1. **URL Exacta**: Hash de URL (actual - MongoDB index)
2. **Contenido Idéntico**: Hash SHA-256 de contenido normalizado
3. **Contenido Similar**: Embeddings + cosine similarity > 0.95 (Fase 3)

---

## 9. Configuración de Implementación

### Archivo de Configuración Recomendado

**Crear**: `etl/config/sources_cto.json`

```json
{
  "version": "2.0",
  "github_governance": [
    {
      "repo": "kubernetes/kubernetes",
      "files": [
        {
          "path": "GOVERNANCE.md",
          "url": "https://raw.githubusercontent.com/kubernetes/community/master/governance.md",
          "priority": "critical"
        }
      ]
    }
  ],
  "engineering_blogs": [
    {
      "name": "Netflix Tech",
      "feed_url": "https://netflixtechblog.com/feed",
      "feed_url_fallback": "https://medium.com/feed/netflix-techblog",
      "difficulty": "medium",
      "target_docs": 30
    }
  ],
  "papers_foundational": [
    {
      "title": "Google File System",
      "year": 2003,
      "pdf_url": "https://research.google.com/archive/gfs-sosp2003.pdf",
      "priority": "critical"
    }
  ],
  "quality_gates": {
    "min_word_count": 500,
    "min_quality_keywords": 2,
    "technical_density_threshold": 0.15
  }
}
```

---

## 10. Comandos de Ejecución

### Spiders

```bash
# Ejecutar todos los spiders del CTO
python run_etl.py --agent cto

# Spider específico
python run_etl.py --spider github
python run_etl.py --spider netflix

# Con límites y nivel de filtrado
python run_etl.py --spider blogs --limit 20 --keyword-level moderate
```

### Validación y Análisis

```bash
# Análisis de MongoDB
python scripts/analyze_db.py

# Verificar archivos raw
Get-ChildItem data\raw\cto\ -Recurse | Measure-Object -Property Length -Sum

# Procesar libros sintéticos
python scripts/process_synthetic_books.py

# Validar calidad de documentos
python scripts/validate_corpus_quality.py
```

---

## Changelog

### v2.0 (2026-01-13)
- Fusión con especificación mejorada por experto externo
- Agregadas URLs directas para todas las fuentes
- Implementados filtros duales (positivos + anti-patrones)
- Definidos KPIs concretos y checklist de Fase 2
- Expandida lista de papers fundacionales (12 papers)
- Agregados blogs adicionales (Airbnb, AWS, Stripe, etc.)
- Roadmap detallado de 4 fases con entregables

### v1.0 (2026-01-13)
- Diseño inicial del corpus
- Fase 1 al 7%: 19/262 documentos
- GitHub, Netflix, ArXiv operativos

---

**Próxima Revisión**: 2026-01-20 (completar Fase 1 → 50 docs)  
**Próximo Hito**: 2026-01-27 (completar Fase 2 → 150 docs)
