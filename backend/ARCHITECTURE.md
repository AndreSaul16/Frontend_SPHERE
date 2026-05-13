# Architecture Overview

**SPHERE Backend** implementa una arquitectura modular guiada por **Domain-Driven Design (DDD)** y **Clean Architecture**. Esto nos permite desacoplar la lógica de negocio central de las implementaciones tecnológicas (bases de datos, APIs de terceros, frameworks web).

## 🧩 Patrones Principales

1. **Inyección de Dependencias:** Usada en FastAPI para inyectar Repositorios y Servicios a los controladores.
2. **Patrón Strategy (Orquestador):** El orquestador de IA selecciona dinámicamente qué agente (Experto, Analista, Board) debe responder en base a la intención del usuario.
3. **Hexagonal Architecture (Ports & Adapters):** El dominio central no conoce FastAPI ni MongoDB. Se comunica mediante interfaces (`Ports`), que son implementadas por las capas de infraestructura (`Adapters`).

## 🔄 Flujo de Datos

1. **Cliente HTTP / WebSocket** -> Petición recibida por FastAPI (`presentation`).
2. **Controlador** -> Llama a un Caso de Uso (`application`).
3. **Orquestador (Application)** -> Valida reglas de negocio (`domain`) y consulta datos a la base de datos a través de repositorios (`infrastructure`).
4. **Respuesta** -> Retornada al cliente en formato JSON estándar.

## ⚙️ Ecosistema Asíncrono
La capa de `infrastructure` hospeda servicios críticos que corren en paralelo:
- **ETL:** Extracción de datos en background (scraping, noticias).
- **n8n:** Ejecuta workflows basados en webhooks que el backend dispara de forma asíncrona.
