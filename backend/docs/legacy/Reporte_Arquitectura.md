# Reporte de Arquitectura - Proyecto SPHERE

Este documento detalla la arquitectura técnica del sistema SPHERE, basada en contenedores Docker y un enfoque de agentes múltiples con LangGraph y RAG.

## 🏗️ Topología del Sistema

La arquitectura está claramente dividida en tres zonas principales para mantener un bajo acoplamiento y separar responsabilidades (Screaming Architecture aplicada a infraestructura):

### 1. Entorno Cliente
- **Frontend:** Aplicación interactiva construida con **React 19**, empaquetada con **Vite**. Maneja el estado global mediante **Zustand** y los estilos con **TailwindCSS**. Interactúa con el backend mediante peticiones HTTP POST al endpoint `/api/v1/chat`.

### 2. Docker Host (Red Virtual: `sphere-network`)
- **Backend (FastAPI):** El núcleo del sistema. Expone la API REST y gestiona el flujo principal y la orquestación.
  - **RAG Engine:** Motor de inyección de contexto. Se conecta a MongoDB Atlas para realizar la búsqueda semántica vectorial.
  - **LangGraph Orchestrator:** El cerebro multi-agente de la aplicación. Cuenta con un *Intelligent Router* que toma decisiones y deriva las tareas a los correspondientes *Agentes Expertos* (CEO, CTO, CFO, CMO).
- **Inferencia Local (`sphere-ml`):** Contenedor diseñado como fallback con **vLLM** para correr modelos locales, preparado para escalabilidad usando CPU/GPU según disponibilidad.

### 3. Servicios Externos y Cloud
- **MongoDB Atlas:** Actúa en doble capacidad: como base de datos documental tradicional para persistencia y como **Vector DB** para el motor RAG.
- **OpenAI API:** Provee el modelo `text-embedding-3-small` indispensable para la generación de embeddings en la base de conocimiento.
- **DeepSeek API:** Provee el LLM principal (`deepseek-chat`) que alimenta la toma de decisiones y las respuestas del motor LangGraph.

---

## 🗺️ Diagrama de Arquitectura

Para visualizar, editar o exportar el diagrama de arquitectura, haz clic en el siguiente enlace. Contiene el código fuente completo incrustado de forma segura:

**👉 [Abrir Diagrama Interactivo de SPHERE en Draw.io](https://app.diagrams.net/?grid=0&pv=0&border=10&edit=_blank#create=%7B%22type%22%3A%22xml%22%2C%22compressed%22%3Atrue%2C%22data%22%3A%227VpRb%2BI4EP4t9xCp%2B4BEkkLZR6C0W6kVVenuSfeCTDIEq06ccwy0%2B%2BtvnDg0idMjQKHb22ur3TCe2PH3zYxnhljuMHy%2BFiRe3HEfmOW0%2FWfLvbQcxz53HEv9tf2XTNJrtzNBIKivlV4FE%2FoTtDBXW1IfkpKi5JxJGpeFHo8i8GRJRoTg67LanLPyqjEJwBBMPMJM6Z%2FUlwsttbtfXwe%2BAQ0Weumec5ENzIj3FAi%2BjPR6luPO059sOCT5XHqjyYL4fF0SEZ%2FEkq5gyBkXeh9kKbkadUdWu28pzbblDgXnsiTKB8LnITDFSA52NvVVM%2BXN5gVEsu5%2BY4o%2FWi28GPJIEhoBPrTTRkmjxTxGcZXpTx5BtuyKsKVmYRRJLiKupk61tEYiX3KekjUNGcFb3UEiiZDakpxzFMwpYymGqao776jfVFHwJyiMdNMfHFnIkKHIVjfjXiZ6HY3HCoSE5zchsqv8VDd%2BDTwEKV7ws57lXDP%2BUv64frU4J%2FebRcHYzru5pWjrCDYzv0kyyjX0b1BoEONz7wnEFKKVwctlOoSybzyR%2BN%2FZA%2FjK9tGVlVupqZN4AQJaEcg1F09fDiHOJ9Cbe7XEeT2YzT%2BAOIxn25hzux%2FGHDxLEBFhtdxNQKyoR7ny0VGqmF6q1ZWb8aV%2FkJPN545Xy5XfnXU7H%2BFk3e1cbWRH50oHyjSa4cVfadRrjxiEKNglbC4T5YAVbr8nSyKoipdXFPk3iVyQWF0uQ9b3pGJmoPCmeO7dkhmwe55QSXmEKjMuJQ8LCn1GAzUgeVwmkS8lw6A%2F3JzE%2BLyDRmRWQv9utFZY7Zqs1pHaOwKnBjdzgXYNkW%2FwYzldhg8ymOFFoC4egHjKDq42d2QKuOZGZ3OTyCU%2FqDoJcfWBMqEl%2BqS6U39%2BJJStaWR6cZqUgK9ZWy9wkklMPDW6xiSu4plltwbb78BFnVt%2F7V64pHsSxt0y45t8qUC5Xcf58fx4cw6OVKDdx41Vuoi8T5OVZ1iLPkK1ijpmr0gi%2B%2Fc3h52mHej553VU9pyZe3gaVE4bdjxWt5%2BqTg3Bp%2FFqElPclR9zmlJcIethNHlECbJj%2BusZLoZ3478rBOzKWxBpUriTezZiomJb701Fra91TsGEIAEyEdCaiuGhf5264%2BvgrwuxvT0xsevM%2FSQYYzQJAlXbGxDf4sh1NtIeC28BGEiISiYOCEoNzpePtH7bNqnZBJ0iNfZp7B9Trprs7wZTCIZZWpZaPhSUij6w4OFsmeycAcx7HtQn9rNe57zTOOcr2dVupFyUSXE7v1BIgucY9z0lAdQdDn0lhqziUnqq4jIOieFobDm4dHv4mF9c5Rd341McGAdwU%2Blk2O0ah6ltZZyCnJBNaTTHXCryzBPDyMl12oXQNUrGV7e3dzjjnDCmQg5eMu6p2qt9Nrz%2Fjvde338%2FkLzdG1mnztTcmvKrNlU7Xi4%2B0k0P64BsPORRwKdEMmL6sGEnd0r5UpVc%2FeyGJtaCZGEYxRIbsqaLuv0HpLU4lhMD8wzVFbv3gjW2D8Ldbi2zzLRuZxvBpiU9zkp1LU%2By89ju7FUkNDKxaidqNyPrlI2sxsZqA%2F5JqgEeQ0ToNE3rt1nKGHX7N1apOvh3M0FMZQvCGfg%2BjYKW20pCwsx%2BziFRpEFX9fQUb1Lij6jpzQ44QJwAPDVj%2BRK1J6i9C8%2F5Ci1VE%2F736XVr0oITt2xGfpCG3rP7fJP2lx1OCJiqxus07fBljwi%2B8U1ipV2NnPKl8LTWa%2BMWa6IAtGK5ZViwATV93oDhQi54wJGN0at0ULaSSs7XkC4BjKivHEtPfdyEOcOw1rW%2BPT7eo%2BR%2BrFoq%2B2BcRrOIc00T57cAW%2B37zbKRepRY6pt4Muf7AV4DaxF1UV%2BLfk64i6NNoM82%2F1ZpeAmCrkiGF5D90C%2FCW4S9pij99Og3NnYSHMeUK73HTw%2FodvvFHb8ZOl6wdlHWq179wFRhz%2FBRBfX%2F2FHAPi1KDegH1tC1Bv3k7yX4ioAJhErStyP1be3702CUxp%2Bei6b4Z5WeQcAor86S9we7Wlz%2BFlhnx9Q0L4kMwIdpiYSRJowZpG8p7IV7zaFYhN6s%2BX4n8FeMhQbw41g1rNLOWvaW0I1upqZZ423W7TwCFWbb9n2o8Emy2Mh%2FBV7SocK7nFq18GqtO%2FoH%22%7D)**