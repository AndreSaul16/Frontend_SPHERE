# 📂 Diseño del Corpus de Conocimiento - CFO (Chief Financial Officer)

**ID del Documento**: `SPHERE-DATA-CFO-004`  
**Responsable**: Sistema ETL SPHERE  
**Estado**: 🟡 En Progreso (3/21 docs procesados)

---

## 1. Visión y Estrategia

### El Objetivo "Golden Standard"

Construir un CFO capaz de navegar desde **Unit Economics** (NDR, CAC/LTV) hasta **Macro Strategy** (ciclos de mercado, primas de riesgo), dominando tanto la **Ciencia de Valuación** (DCF, WACC) como el **Arte de la Asignación de Capital** (cuándo hacer buybacks vs. dividendos vs. M&A).

### Filosofía del Corpus

**"Rigor sobre Intuición"**: Las decisiones financieras requieren modelos cuantitativos, no feeling.

**Principios**:
- ✅ **Evidencia Empírica**: Prioridad a data points reales (10-Ks, Damodaran ERP data)
- ✅ **Densidad Técnica**: Fórmulas, benchmarks, frameworks aplicables
- ✅ **Dualidad Operativa/Estratégica**: Balance entre métricas SaaS y visión macro
- ❌ **Bloqueo de Fluff**: Evitar contenido "motivacional" o consejos genéricos

---

## 2. Arquitectura de Datos (Pipeline Polimórfico)

### 🟤 BRONZE (Landing Zone)
- **Formato**: Original (`.html`, `.pdf`)
- **Almacenamiento**: File System (`data/raw/cfo/`)
- **Propósito**: Auditoría y backup
- **Retención**: Indefinida

### ⚪ SILVER (Knowledge Base)
- **Formato**: Markdown + Metadata Financiera
- **Almacenamiento**: MongoDB Atlas (`collection: knowledge_base`)
- **Propósito**: RAG y búsquedas semánticas
- **Schema**:
```json
{
  "source": "David Skok - For Entrepreneurs",
  "title": "SaaS Metrics 2.0",
  "url": "https://www.forentrepreneurs.com/saas-metrics-2/",
  "file_path": "data/raw/cfo/metrics/...",
  "content_markdown": "# Content...",
  "tags": ["cac", "ltv", "unit-economics"],
  "agent_target": "CFO",
  "curated_category": "saas_metrics",
  "core_concept": "CAC, LTV, Churn, Unit Economics"
}
```

### 🟡 GOLD (Training Set)
- **Formato**: Pares JSONL para fine-tuning
- **Fase**: Futura

---

## 3. Inventario Maestro de Fuentes

> **Estrategia**: Omitimos 7 libros sintéticos (requieren Deep Research manual) para enfocarnos en **21 fuentes digitales** automatizables.

### A. Métricas SaaS (7 recursos → 3 procesados)

| Recurso | URL | Status | Docs |
|---------|-----|--------|------|
| **David Skok - SaaS Metrics** | `https://www.forentrepreneurs.com/saas-metrics-2/` | ✅ Procesado | 1 |
| **OpenView - Rule of 40** | `https://openviewpartners.com/blog/rule-of-40/` | ⚠️ Error conexión | 0 |
| **ChartMogul - NDR Guide** | `https://chartmogul.com/blog/...` | ❌ 404 | 0 |
| a16z - Unit Economics | `https://a16z.com/` | ⏳ Pendiente | 0 |
| SaaS Capital - Burn Rate | `https://www.saas-capital.com/` | ⏳ Pendiente | 0 |
| ProfitWell - Cohort Analysis | `https://www.profitwell.com/recur/` | ⏳ Pendiente | 0 |
| Bessemer - Cloud Index | `https://www.bvp.com/` | ⏳ Pendiente | 0 |

**Total actual**: 1/7

---

### B. Regulación y Reporting (7 docs → 1 procesado)

| Documento | Fuente | URL | Status |
|-----------|--------|-----|--------|
| **Berkshire Annual Report** | Berkshire Hathaway | `berkshirehathaway.com/2023ar/` | ✅ Procesado | 
| Salesforce 10-K | SEC EDGAR | `sec.gov/edgar/` | ⏳ Pendiente |
| ASC 606 Summary | FASB | `fasb.org/` | ❌ 403 Forbidden |
| IFRS 16 Guide | IFRS Foundation | `ifrs.org/` | ⏳ Pendiente |
| Non-GAAP Guidelines | SEC | Public | ⏳ Pendiente |
| SOX Compliance | Public resources | Multiple | ⏳ Pendiente |
| Board Deck Template | Sequoia/a16z | `sequoiacap.com/` | ❌ Error conexión |

**Total actual**: 1/7

---

### C. Macroeconomía (7 análisis → 1 procesado)

| Análisis | Autor | URL | Status |
|----------|-------|-----|--------|
| **Risk Revisited** | Howard Marks | `oaktreecapital.com/insights/` | ✅ Procesado |
| ERP Data | Aswath Damodaran | `stern.nyu.edu/~adamodar/` | ❌ DNS Timeout |
| Economic Machine | Ray Dalio | `principles.com/` | ⏳ Pendiente |
| Inflation Swindles | Warren Buffett | Berkshire letters | ⏳ Pendiente |
| Crucible Moments | Sequoia | Public memo | ⏳ Pendiente |
| Global Outlook | BlackRock | `blackrock.com/` | ⏳ Pendiente |
| IPO Process Guide | Public | Multiple banks | ⏳ Pendiente |

**Total actual**: 1/7

---

## 4. Estado Actual

### Documentos Procesados

| Categoría | Actual | Objetivo | % |
|-----------|--------|----------|---|
| **SaaS Metrics** | 1 | 7 | 14% |
| **Regulatory** | 1 | 7 | 14% |
| **Macro** | 1 | 7 | 14% |
| **TOTAL** | **3** | **21** | **14%** |

### Problemas Detectados

1. ⚠️ **Errores de Conexión Temporales**:
   - MongoDB SSL handshake failed (problema temporal)
   - DNS timeouts en algunos sitios (Damodaran)
   - Connection reset errors (OpenView, ChartMogul)

2. ❌ **URLs Inaccesibles**:
   - ChartMogul NDR guide (404)
   - FASB ASC 606 (403 Forbidden)
   - Sequoia board deck (connection error)

3. ✅ **Éxitos**:
   - David Skok SaaS Metrics 2.0 ✅
   - Berkshire Hathaway Annual Report 2023 ✅
   - Howard Marks "Risk Revisited" ✅

---

## 5. Comandos de Ejecución

### Spiders

```bash
# Ejecutar todos los spiders CFO
python -m etl.agents.cfo

# Modo rápido (1 doc por spider)
python -m etl.agents.cfo --quick

# Con límite personalizado
python -m etl.agents.cfo --limit 3

# Spiders individuales
python -m etl.agents.cfo.saas_metrics_spider
python -m etl.agents.cfo.regulatory_spider
python -m etl.agents.cfo.macro_spider
```

### Análisis

```bash
# Análisis de MongoDB
python etl/scripts/analyze_db.py

# Verificar archivos locales
Get-ChildItem data\raw\cfo\ -Recurse -File

# Validar calidad
python etl/scripts/validate_corpus_quality.py --agent cfo
```

---

## 6. Próximos Pasos

### Inmediatos
- [ ] Resolver problemas de conexión MongoDB
- [ ] Buscar URLs alternativas para recursos inaccesibles
- [ ] Re-ejecutar con más reintentos y backoff

### Corto Plazo
- [ ] Completar 21/21 fuentes digitales
- [ ] Agregar más fuentes de SaaS metrics
- [ ] Procesar más annual reports (Salesforce, Snowflake)

### Futuro
- [ ] Generar 7 libros sintéticos con Deep Research
- [ ] Alcanzar 30+ documentos totales

---

## Changelog

### v0.1 (2026-01-16)
- ✅ 3 spiders implementados (metrics, regulatory, macro)
- ✅ 3 documentos procesados (David Skok, Berkshire, Howard Marks)
- ⚠️ Problemas de conexión detectados
- 🟡 14% de objetivo alcanzado (3/21 docs)

---

**Próxima Revisión**: 2026-01-23  
**Objetivo Fase 1**: 10 documentos (50% de 21)