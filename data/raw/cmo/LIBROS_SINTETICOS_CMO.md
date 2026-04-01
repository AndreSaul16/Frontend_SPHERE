# 📚 Libros Sintéticos para CMO - Deep Research

Lista de libros que debes generar con Gemini Deep Research para el agente CMO.

---

## 🎯 Canon Estratégico (7 Libros)

### 1. **"Influence: The Psychology of Persuasion"** - Robert Cialdini
- **Tema**: 6 principios de influencia (reciprocidad, escasez, autoridad, coherencia, simpatía, consenso social)
- **Valor para CMO**: Fundamentos de persuasión aplicados a marketing
- **Prompt Deep Research**:
  ```
  Analiza "Influence: The Psychology of Persuasion" de Robert Cialdini. 
  Extrae los 6 principios de influencia con ejemplos específicos en marketing.
  Incluye aplicaciones prácticas para growth marketing y conversión.
  Formato: resumen denso con fórmulas aplicables y anti-patrones a evitar.
  ```

### 2. **"Thinking, Fast and Slow"** - Daniel Kahneman
- **Tema**: Sistema 1 (rápido/intuitivo) vs Sistema 2 (lento/analítico)
- **Valor para CMO**: Cómo los consumidores toman decisiones de compra
- **Prompt Deep Research**:
  ```
  Analiza "Thinking, Fast and Slow" de Daniel Kahneman.
  Enfócate en sesgos cognitivos aplicables a marketing (anclaje, disponibilidad, efecto halo).
  Incluye implicaciones para pricing, messaging y diseño de funnels.
  Omite la parte de economía conductual no relacionada con marketing.
  ```

### 3. **"How Brands Grow"** - Byron Sharp
- **Tema**: Leyes empíricas del crecimiento de marcas (Mental Availability, Physical Availability)
- **Valor para CMO**: Desmitifica mitos de marketing (loyalty, diferenciación)
- **Prompt Deep Research**:
  ```
  Analiza "How Brands Grow" de Byron Sharp.
  Extrae las leyes empíricas del crecimiento: Mental Availability, Physical Availability,
  Duplication of Purchase Law, y la crítica a la segmentación excesiva.
  Incluye evidencia cuantitativa y contradicciones con marketing "tradicional".
  ```

### 4. **"Crossing the Chasm"** - Geoffrey Moore
- **Tema**: Ciclo de adopción tecnológica (Early Adopters → Early Majority)
- **Valor para CMO**: Estrategia Go-to-Market para productos tech
- **Prompt Deep Research**:
  ```
  Analiza "Crossing the Chasm" de Geoffrey Moore.
  Enfócate en las diferencias entre segmentos de adopción (innovators, early adopters, etc.).
  Extrae tácticas específicas para "cruzar el abismo" hacia el mainstream.
  Incluye frameworks de positioning y messaging para cada etapa.
  ```

### 5. **"Contagious: Why Things Catch On"** - Jonah Berger
- **Tema**: Framework STEPPS (Social Currency, Triggers, Emotion, Public, Practical Value, Stories)
- **Valor para CMO**: Mecánica de viralidad y word-of-mouth
- **Prompt Deep Research**:
  ```
  Analiza "Contagious: Why Things Catch On" de Jonah Berger.
  Extrae el framework STEPPS con ejemplos de cada elemento.
  Incluye aplicaciones a product-led growth y viral loops.
  Omite anécdotas sin valor táctico.
  ```

### 6. **"Building a StoryBrand"** - Donald Miller
- **Tema**: Framework SB7 (el cliente es el héroe, no la marca)
- **Valor para CMO**: Claridad en messaging y narrativa
- **Prompt Deep Research**:
  ```
  Analiza "Building a StoryBrand" de Donald Miller.
  Extrae el framework SB7 completo: Character, Problem, Guide, Plan, Call to Action, Failure, Success.
  Incluye ejemplos de antes/después de aplicar el framework.
  Enfócate en aplicaciones prácticas para landing pages y pitch decks.
  ```

### 7. **"Positioning: The Battle for Your Mind"** - Al Ries & Jack Trout
- **Tema**: Cómo ocupar un espacio único en la mente del consumidor
- **Valor para CMO**: Fundamentos de diferenciación y category design
- **Prompt Deep Research**:
  ```
  Analiza "Positioning: The Battle for Your Mind" de Al Ries y Jack Trout.
  Extrae principios de positioning: first-mover advantage, ladder mental, reposicionamiento.
  Incluye ejemplos clásicos (Avis "We're #2") y aplicaciones modernas.
  Relaciona con category design contemporáneo.
  ```

---

## 📋 Instrucciones de Generación

### Paso 1: Generar con Deep Research
Para cada libro:
1. Abre Gemini 2.0 con Deep Research
2. Usa el prompt específico de arriba
3. Espera a que genere el documento completo (10-15 min)
4. Descarga como Markdown

### Paso 2: Guardar Archivos
```bash
# Estructura
data/synthetic/cmo/books/
├── influence_robert_cialdini.md
├── thinking_fast_and_slow_kahneman.md
├── how_brands_grow_byron_sharp.md
├── crossing_the_chasm_moore.md
├── contagious_jonah_berger.md
├── building_a_storybrand_miller.md
└── positioning_ries_trout.md
```

### Paso 3: Procesar con Script
Una vez generados todos, ejecutar:
```bash
python etl/scripts/process_synthetic_books.py --agent cmo
```

---

## ✅ Checklist de Progreso

- [ ] Influence (Cialdini)
- [ ] Thinking Fast and Slow (Kahneman)
- [ ] How Brands Grow (Sharp)
- [ ] Crossing the Chasm (Moore)
- [ ] Contagious (Berger)
- [ ] Building a StoryBrand (Miller)
- [ ] Positioning (Ries & Trout)

---

## 🎯 Valor Esperado

**Total**: 7 libros sintéticos  
**Tamaño estimado**: ~50-100 KB cada uno (~500 KB total)  
**Tiempo de generación**: ~2 horas total (15 min por libro)  
**Impacto en corpus**: +7 documentos de máxima densidad

**Con estos 7 + los 27 actuales = 34 documentos CMO** ✅

---

## 📌 Notas

1. **Deep Research automático**: Gemini buscará fuentes primarias y secundarias
2. **Limpieza posterior**: El script `process_synthetic_books.py` limpiará referencias
3. **Calidad esperada**: Resúmenes densos con frameworks aplicables, no reseñas superficiales
4. **Omitir**: Anécdotas sin valor táctico, relleno narrativo, secciones irrelevantes

---

**Siguiente paso**: Generar el primer libro (recomiendo empezar con Cialdini por ser el más fundamental)
