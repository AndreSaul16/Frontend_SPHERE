# 📂 Diseño del Corpus de Conocimiento - CMO (Chief Marketing Officer)

**ID del Documento**: `SPHERE-DATA-CMO-003`  
**Responsable**: Sistema ETL SPHERE  
**Estado**: 🟢 Listo para Ingesta

---

## 1. Visión y Estrategia

### El Objetivo "Golden Standard"

Construir el cerebro de un CMO "Full-Stack" que opera en la intersección de la **Psicología Conductual** (Sistema 1 vs. Sistema 2), la **Ingeniería de Crecimiento** (Loops vs. Funnels) y la **Narrativa Estratégica**. No queremos un agente que genere copies genéricos, sino uno capaz de diseñar sistemas de crecimiento compuesto y defender presupuestos con econometría.

### Filosofía del Corpus

**"Ciencia sobre Creatividad"**: El marketing moderno no es arte, es psicología aplicada a escala.

**Principios**:
- ✅ Evidencia Empírica: Prioridad a leyes inmutables (Byron Sharp, Binet & Field) sobre tendencias pasajeras
- ✅ Densidad Táctica: Preferimos un post-mortem de una campaña fallida que 100 artículos de "Tendencias 2026"
- ✅ Dualidad: El corpus debe equilibrar "Brand" (Largo plazo/Emocional) y "Performance" (Corto plazo/Racional)
- ❌ Bloqueo de "Humo": Filtros agresivos contra contenido de "Gurús", "Get rich quick" y métricas de vanidad

---

## 2. Arquitectura de Datos (Pipeline Polimórfico)

Implementamos la arquitectura Medallion estricta para garantizar trazabilidad:

### 🟤 BRONZE (Landing Zone)
- **Formato**: Original (`.html`, `.pdf`, `.md`)
- **Almacenamiento**: File System (`data/raw/cmo/`)
- **Propósito**: Auditoría y recuperación ante fallos de parseo
- **Retención**: Indefinida (backups inmutables)

### ⚪ SILVER (Knowledge Base)
- **Formato**: Markdown Limpio + Metadata Semántica
- **Almacenamiento**: MongoDB Atlas (`collection: knowledge_base`)
- **Propósito**: Fuente para RAG y búsquedas semánticas
- **Schema**:
```json
{
  "source": "Andrew Chen (a16z)",
  "title": "BRAINDUMP ON VIRAL LOOPS",
  "url": "https://andrewchen.substack.com/p/braindump-on-viral-loops",
  "file_path": "data/raw/cmo/blogs/AndrewChen_braindump-on-viral-loops.html",
  "content_markdown": "# Title\n\nContent...",
  "tags": ["network-effects", "virality", "growth", "a16z"],
  "agent_target": "CMO",
  "curated_category": "marketing_blog",
  "ingested_at": "2026-01-16",
  "published_date": "2025-11-05",
  "metadata": {
    "marketing_funnel_stage": "retention",
    "psychological_trigger": "reciprocity",
    "complexity_level": "strategic"
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

> **⚠️ Instrucción de Implementación**: Estas URLs están listas para copiar a `config/sources_cmo.json` o directamente a los spiders.

### A. Engineering Blogs (11 docs → 50 objetivo)

**Foco**: Growth engineering, data-driven marketing, y estrategias validadas por datos.

| Empresa/Blog | Feed URL | Enfoque Principal | Dificultad | Docs Objetivo | Estado |
|--------------|----------|-------------------|------------|---------------|--------|
| **Reforge** | `https://www.reforge.com/blog/feed` | Growth Loops, Product Strategy | 🔴 Alta | 10 | ⚠️ Feed bloqueado |
| **Andrew Chen (a16z)** | `https://andrewchen.substack.com/feed` | Network Effects, Virality | 🟢 Baja | 15 | ✅ 5 docs |
| **Moz Blog** | `https://moz.com/blog/feed` | SEO Técnico | 🟢 Baja | 10 | ✅ 1 doc |
| **Ahrefs Blog** | `https://ahrefs.com/blog/feed` | Data-driven SEO | 🟢 Baja | 10 | ✅ 4 docs |
| **Kellblog (Dave Kellogg)** | `https://kellblog.com/feed/` | SaaS Metrics, B2B Marketing | 🟡 Media | 5 | ✅ 1 doc |

**Total Blogs Actuales**: **11 documentos**  
**Total Blogs Objetivo**: **50 documentos**

---

### B. Frameworks Estratégicos (10 docs → 15 objetivo)

**Foco**: Modelos mentales, investigación académica, y frameworks aplicables.

#### B1. PDFs de Investigación (5 docs implementados)

| Framework | Autor/Fuente | Concepto Clave | URL Directa | Estado |
|-----------|--------------|----------------|-------------|--------|
| **The Long and the Short of It** | Binet & Field (IPA) | Ratio Marca (60%) vs Performance (40%) | [PDF](https://screenforce.nl/wp-content/uploads/2015/11/the-long-and-short-of-it.pdf) | ✅ |
| **The Messy Middle** | Google Research | Modelo de decisión Exploración/Evaluación | [PDF](https://www.thinkwithgoogle.com/_qs/documents/9998/Decoding_Decisions_The_Messy_Middle_of_Purchase_Behavior.pdf) | ✅ |
| **StoryBrand Framework (SB7)** | Donald Miller | El cliente es el héroe | [PDF](https://storybrand.com/downloads/your-brand-is-not-the-hero.pdf) | ✅ |
| **Blue Ocean Strategy** | Kim & Mauborgne | Competir en espacios no disputados | [PDF](https://info.eaglenet.jbu.edu/depts/odl/om/resources/om3263/BOSHBR.pdf) | ✅ |
| **HubSpot Inbound Marketing** | HubSpot | Inbound vs Outbound | [PDF](https://www.hubspot.com/hs-fs/hub/53/file-13201504-pdf/docs/hubspotinboundmarketingworkbook-pdf.pdf) | ✅ |

#### B2. Web-based Frameworks (5 docs implementados)

| Framework | Fuente | Concepto Clave | URL Directa | Estado |
|-----------|---------|----------------|-------------|--------|
| **See-Think-Do-Care** | Avinash Kaushik | Intent-based Marketing | [Link](https://www.kaushik.net/avinash/see-think-do-content-marketing-measurement-business-framework/) | ✅ |
| **Law of Shitty Clickthroughs** | Andrew Chen | Decadencia de canales | [Link](https://andrewchen.com/the-law-of-shitty-clickthroughs/) | ✅ |
| **Product/Market Fit** | Marc Andreessen | Definición canónica de PMF | [Link](https://pmarchive.com/guide_to_startups_part4.html) | ✅ |
| **Do Things that Don't Scale** | Paul Graham (YC) | Estrategia inicial | [Link](https://paulgraham.com/ds.html) | ✅ |
| **1,000 True Fans** | Kevin Kelly | Monetización sostenible | [Link](https://kk.org/thetechnium/1000-true-fans/) | ✅ |

**Total Frameworks Actuales**: **10 documentos**  
**Total Frameworks Objetivo**: **15 documentos**

---

### C. "War Room": Casos de Estudio Reales (6 docs → 15 objetivo)

**Foco**: Ingeniería inversa de tácticas exitosas con métricas reales.

| Empresa | Táctica Clave | Categoría | Recurso / URL | Estado |
|---------|---------------|-----------|---------------|--------|
| **Airbnb** | Craigslist Integration (Technical Growth Hack) | Technical Hack | [Link](https://growthhackers.com/growth-studies/airbnb/) | ✅ |
| **Dropbox** | Viral Loop (Referral Program) | Viral Loop | [Link](https://viral-loops.com/blog/dropbox-grew-3900-simple-referral-program/) | ✅ |
| **Salesforce** | "No Software" (Enemy creation) | Category Design | [Link](https://www.salesforce.com/news/stories/the-history-of-salesforce/) | ✅ |
| **HubSpot** | Inbound Marketing (Category Creation) | Content-Led Growth | [PDF](https://www.hubspot.com/hs-fs/hub/53/file-13201504-pdf/docs/hubspotinboundmarketingworkbook-pdf.pdf) | ✅ |
| **Red Bull** | Media House Strategy (Content as Product) | Content Strategy | [PDF](https://www.uni-potsdam.de/fileadmin/projects/professional-services/downloads/skripte-ws/Wintersemester2018/MS270_Red_Bull_Business_Case_080415.pdf) | ✅ |
| **Liquid Death** | Branding Disruptivo (Death to Plastic) | Counter-positioning | [PDF](https://h16m.com/wp-content/uploads/2024/06/Liquid-Death-Case-study.pdf) | ✅ |
| **Slack** | Product-Led Growth (Bottom-up) | PLG | [PDF](https://openviewpartners.com/wp-content/uploads/2018/07/OpenView-Product-Led-Growth-Playbook.pdf) | ✅ |

**Total Case Studies Actuales**: **6 documentos**  
**Total Case Studies Objetivo**: **15 documentos**

---

## 4. Especificación de Filtrado (Quality Gates)

Para el CMO, el ruido es "contenido aspiracional sin datos".

### Filtros de Palabras Clave (Positivos)

**Solo ingerir si el contenido menciona al menos 2 de estas**:

```python
KEYWORDS_QUALITY = [
    # Growth Engineering
    'growth loops', 'growth hacking', 'viral', 'virality', 'network effects',
    'retention', 'activation', 'conversion', 'funnel', 'pirate metrics',
    'product-market fit', 'pmf', 'cohort analysis',
    
    # Consumer Psychology
    'behavioral', 'psychology', 'cognitive bias', 'persuasion', 'influence',
    'system 1', 'system 2', 'heuristics', 'mental availability',
    
    # Strategy & Frameworks
    'positioning', 'category design', 'messaging', 'narrative',
    'brand equity', 'differentiation', 'segmentation',
    
    # Data & Analytics
    'attribution', 'ltv', 'cac', 'unit economics', 'cohort',
    'experimentation', 'a/b test', 'causal inference'
]
```

### Filtros de Exclusión (Anti-Patrones)

**Descartar inmediatamente si detecta**:

```python
KEYWORDS_BLOCK = [
    # Contenido Superficial
    'top 10', 'top 5', 'best tools', 'for beginners',
    'tutorial for beginners', 'introduction to', 'getting started with',
    
    # Contenido no técnico
    'get rich quick', 'secret formula', 'hack your way',
    'influencer tips', 'motivational', 'mindset shift',
    
    # Métricas de vanidad
    'viral growth hack', 'go viral', 'get famous',
    'boost engagement', 'increase followers'
]
```

---

## 5. Estado Actual vs. Objetivo

### Métricas de Cobertura

| Categoría | Docs Actuales | Docs Objetivo | % Completado | Estado |
|-----------|---------------|---------------|--------------|--------|
| **Engineering Blogs** | 11 | 50 | 22% | 🟡 En progreso |
| **Frameworks (PDF)** | 5 | 8 | 63% | 🟢 On track |
| **Frameworks (Web)** | 5 | 7 | 71% | 🟢 On track |
| **Case Studies** | 6 | 15 | 40% | 🟡 En progreso |
| **TOTAL** | **27** | **80** | **34%** | 🟡 **Fase 1 MVP** |

### KPIs de Fase 2 (Próximo Hito)

Sabremos que hemos completado la **Fase 2** cuando:

- [ ] **Total Documentos**: ≥ 60
- [x] **Frameworks Fundacionales**: 10/10 procesados ✅
- [ ] **Cobertura de Blogs**: Al menos 3 artículos de cada fuente
- [x] **Calidad Semántica**: Ningún documento < 500 palabras (excepto manifiestos) ✅
- [x] **Diversidad Temática**: Cada tema del corpus con ≥ 3 documentos ✅
- [x] **Bronze Layer**: 100% de documentos tienen backup en disco ✅

---

## 6. Comandos de Ejecución

### Spiders

```bash
# Ejecutar todos los spiders del CMO
python -m etl.agents.cmo

# Modo rápido (2 docs por fuente)
python -m etl.agents.cmo --quick

# Modo personalizado
python -m etl.agents.cmo --blogs 10 --frameworks 5 --case-studies 10

# Spider específico
python -m etl.agents.cmo.blogs_spider
python -m etl.agents.cmo.frameworks_spider
python -m etl.agents.cmo.case_studies_spider
```

### Validación y Análisis

```bash
# Validar URLs antes de ingesta
python etl/scripts/url_validator.py --corpus data/raw/cmo/corpus_definition_cmo.md

# Análisis de MongoDB
python etl/scripts/analyze_db.py

# Verificar archivos raw
Get-ChildItem data\raw\cmo\ -Recurse | Measure-Object -Property Length -Sum

# Validar calidad de documentos
python etl/scripts/validate_corpus_quality.py --agent cmo
```

---

## Changelog

### v1.0 (2026-01-16)
- ✅ Sistema ETL completo implementado
- ✅ 27 documentos procesados (11 blogs + 10 frameworks + 6 case studies)
- ✅ Verificador de URLs con 85.3% de éxito
- ✅ Detección de duplicados funcionando
- ✅ Arquitectura Medallion Bronze + Silver operativa
- ⚠️ Reforge feed bloqueado (requiere scraping directo)

---

**Próxima Revisión**: 2026-01-23 (completar Fase 2 → 60 docs)  
**Próximo Hito**: 2026-02-06 (MVP completo → 80 docs)