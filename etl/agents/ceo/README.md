# Spiders del CEO

Spiders especializados para el Chief Executive Officer (CEO).

## Spiders Disponibles

### 1. McKinsey Spider (`mckinsey_spider.py`)

Extrae artículos de estrategia empresarial de McKinsey Featured Insights.

**Fuente**: https://www.mckinsey.com/featured-insights

**Tipo de contenido**:
- Estrategia empresarial
- Transformación digital
- Consultoría de alto nivel

**Datos guardados en**: `data/raw/ceo/`

## Uso

### Ejecutar todos los spiders del CEO

```bash
cd c:\Users\Saul\Documents\PROGRAMACION\SPHERE\etl
python run_etl.py --agent ceo
```

### Ejecutar spider específico

```bash
python agents\ceo\mckinsey_spider.py
```

## Notas

- McKinsey puede tener rate limiting estricto (delay de 3 segundos entre requests)
- El contenido es de alta densidad estratégica
- Solo se procesan artículos con >1000 caracteres de contenido limpio
