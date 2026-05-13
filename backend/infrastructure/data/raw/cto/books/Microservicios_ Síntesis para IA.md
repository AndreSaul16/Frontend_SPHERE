# **Protocolo de Arquitectura Distribuida: Síntesis Estratégica de "Building Microservices" (2ª Edición)**

## **Introducción Ejecutiva: El Mandato del Arquitecto en la Segunda Era**

Este informe constituye la base de conocimiento fundamental para un Agente de Inteligencia Artificial diseñado para operar como un Arquitecto de Software Principal. Se basa en una síntesis exhaustiva y crítica de la segunda edición de *Building Microservices* de Sam Newman (2021). A diferencia de su predecesora de 2015, esta edición refleja una industria que ha madurado a través del dolor de las implementaciones fallidas. Como CTO con dos décadas de experiencia, presento este análisis no como un resumen pasivo, sino como un conjunto de **marcos de decisión ejecutables**.

El objetivo de este documento es entrenar al Agente para que trascienda la mera codificación y opere en el nivel de los "trade-offs" arquitectónicos. La premisa central que el Agente debe internalizar es el escepticismo: los microservicios no son el objetivo; son una opción arquitectónica con un alto costo ("Microservice Premium") que solo se justifica bajo condiciones específicas de escala organizacional y complejidad de dominio.1

El informe está estructurado para guiar al Agente a través de la anatomía de las decisiones, desde la descomposición molecular de los límites del servicio hasta la orquestación de transacciones distribuidas, proporcionando heurísticas binarias y gradientes de riesgo para cada escenario.

## ---

**Parte I: Fundamentos Axiomáticos y la Prima de los Microservicios**

Para que un Agente pueda razonar sobre arquitectura, primero debe comprender las definiciones no negociables que separan una arquitectura de microservicios funcional de un "monolito distribuido" caótico.

### **1.1 La Definición Operativa y la Regla de Oro**

Sam Newman redefine los microservicios en esta segunda edición con una precisión quirúrgica que el Agente debe adoptar como su axioma principal: **Los microservicios son servicios independientemente desplegables que están modelados alrededor de un dominio de negocio**.4

El Agente debe aplicar la "Regla de Oro" en cualquier evaluación de sistemas:

"¿Puedes realizar un cambio en un servicio y desplegarlo por sí mismo sin cambiar nada más?".7

Si la respuesta es negativa, el sistema no es una arquitectura de microservicios, independientemente de la tecnología utilizada (Kubernetes, Docker, etc.). El Agente debe clasificar cualquier sistema que requiera despliegues coordinados (lockstep deployment) como una violación arquitectónica crítica. La independencia de despliegue no es negociable; es la característica definitoria que permite a las organizaciones escalar sus equipos de desarrollo sin que se bloqueen entre sí.

### **1.2 El Concepto de "Microservice Premium"**

El Agente debe ser entrenado para evitar la "envidia de microservicios". Newman, apoyado por Martin Fowler, introduce el concepto de "Microservice Premium".1 Esto se refiere al costo base inherente de complejidad que introduce una arquitectura distribuida:

* Necesidad de automatización de despliegue avanzada.  
* Gestión de la consistencia eventual.  
* Complejidad en la depuración y trazabilidad.  
* Latencia de red y manejo de fallos parciales.

Heurística de Decisión para el Agente:  
El Agente debe evaluar la complejidad del dominio y el tamaño del equipo antes de recomendar microservicios.

1. **Evaluación de Complejidad:** Si el dominio es simple o el equipo es pequeño, el costo de la "prima" excederá los beneficios de productividad.  
2. **Acción Recomendada:** En escenarios de baja complejidad, el Agente debe recomendar un **Monolito Modular**. Solo cuando el monolito se vuelve inmanejable debido a la fricción organizacional (demasiados desarrolladores tocando el mismo código base), se justifica pagar la prima de los microservicios.8

### **1.3 Cohesión y Acoplamiento: Las Fuerzas Físicas del Software**

El diseño de sistemas distribuidos se rige por dos fuerzas opuestas. El Agente debe optimizar para **Alta Cohesión** y **Bajo Acoplamiento**.

#### **1.3.1 Cohesión: La Fuerza de la Unidad**

La cohesión es la medida de cuán relacionadas están las partes dentro de un módulo.

* **Definición:** "El código que cambia junto, permanece junto".10  
* **Análisis del Agente:** El Agente debe inspeccionar el historial de commits o los patrones de cambio. Si una nueva funcionalidad de negocio (ej. "Añadir impuestos internacionales") requiere tocar tres servicios diferentes, el sistema tiene **Baja Cohesión**. Esto es un síntoma de límites de servicio mal definidos.  
* **Objetivo:** Agrupar la lógica de negocio relacionada en un solo límite para minimizar la "cirugía de escopeta" (shotgun surgery) donde un cambio de negocio salpica múltiples servicios.

#### **1.3.2 Acoplamiento: La Amenaza a la Autonomía**

El acoplamiento mide cuánto depende un servicio de otro. Newman categoriza los tipos de acoplamiento, y el Agente debe ser capaz de identificar y mitigar cada uno.5

**Tabla 1.1: Matriz de Evaluación de Acoplamiento para el Agente**

| Tipo de Acoplamiento | Descripción Técnica | Nivel de Riesgo | Acción del Agente |
| :---- | :---- | :---- | :---- |
| **Acoplamiento de Dominio** | Un servicio llama explícitamente a otro para completar una función (ej. Order llama a Payment). | Aceptable | **Permitir**, pero minimizar. Usar contratos de consumidor (CDCs) para prevenir roturas. |
| **Acoplamiento de Paso (Pass-Through)** | Un servicio transfiere datos a otro sin usarlos, solo para que lleguen a un tercero. | Medio | **Refactorizar**. El intermediario no debe conocer la estructura de los datos. Pasar como "blob" opaco o conectar A con C directamente. |
| **Acoplamiento Común** | Dos servicios comparten una fuente de datos mutable (misma base de datos o memoria compartida). | **Crítico** | **Prohibir**. Es la causa principal de rigidez. Recomendar dividir la base de datos o crear un servicio custodio. |
| **Acoplamiento de Contenido** | Un servicio accede y modifica los internos de otro (ej. UPDATE directo en la tabla de otro servicio). | **Fatal** | **Bloquear**. Viola el principio de ocultación de información. Forzar el uso de APIs públicas. |

El Agente debe internalizar que el **Ocultamiento de Información** (Information Hiding) de David Parnas es el mecanismo principal para lograr bajo acoplamiento. Un servicio debe ocultar sus detalles de implementación (especialmente su esquema de base de datos) para poder evolucionar sin romper a sus consumidores.4

## ---

**Parte II: Modelado de Límites con Diseño Guiado por el Dominio (DDD)**

El desafío más grande no es tecnológico, sino la descomposición correcta del sistema. Newman aboga firmemente por el uso de *Domain-Driven Design* (DDD) para encontrar las costuras naturales del software.10 El Agente utilizará DDD como su "lente" principal para segmentar arquitecturas.

### **2.1 El Contexto Acotado (Bounded Context)**

El concepto central para la toma de decisiones del Agente es el **Contexto Acotado**.

* **Definición:** Es un límite explícito dentro de un dominio donde un modelo particular aplica y tiene un significado inequívoco.13  
* **Aplicación:** El Agente debe buscar la "polisemia" (múltiples significados) en el lenguaje de la organización para identificar límites.

Escenario Simulado: El Caso MusicCorp  
Para entrenar al Agente, utilizamos el ejemplo canónico de "MusicCorp" presentado en el libro.14

* *Situación:* MusicCorp gestiona ventas de música. Existe una entidad llamada "Cliente".  
* *Análisis Lingüístico:*  
  * Para el equipo de **Ventas**, un "Cliente" es alguien con un historial de compras y preferencias de marketing.  
  * Para el equipo de **Envíos/Almacén**, un "Cliente" es simplemente una etiqueta de dirección y un destinatario.  
  * Para el equipo de **Soporte**, un "Cliente" es un ticket con un nivel de servicio (SLA).  
* *Error Común:* Crear un único servicio "CustomerService" con una clase gigante que contenga todos estos atributos.  
* *Decisión del Agente:* Identificar que "Cliente" es un concepto polisemántico. Recomendar la creación de Contextos Acotados separados (Ventas, Envíos, Soporte). Cada contexto tendrá su propia representación de "Cliente" (quizás compartiendo solo un ID). Esto elimina el acoplamiento entre equipos dispares.

### **2.2 Agregados como Átomos de Diseño**

Dentro de los Contextos Acotados, el Agente debe identificar **Agregados**.

* **Definición:** Un clúster de objetos de dominio que pueden tratarse como una unidad. Cada agregado tiene una raíz (Aggregate Root).6  
* **Regla de Diseño:** Un microservicio debe contener uno o más agregados completos. Nunca se debe dividir un agregado entre dos servicios. Las transacciones deben ser atómicas dentro de un agregado.  
* **Heurística:** Los agregados y los contextos acotados proporcionan la unidad de cohesión con interfaces bien definidas; son los candidatos naturales para convertirse en microservicios.10

## ---

**Parte III: Estrategias de Descomposición y Migración (Del Monolito al Microservicio)**

La transición de un monolito a microservicios es una operación de alto riesgo. El Agente debe rechazar categóricamente las reescrituras tipo "Big Bang".16 En su lugar, debe aplicar patrones evolutivos, siendo el más prominente el **Strangler Fig Pattern**.

### **3.1 Patrón Strangler Fig (Higuera Estranguladora)**

Este patrón, inspirado en las higueras que crecen alrededor de un árbol anfitrión hasta matarlo, es el método estándar para la migración segura. El Agente debe ser capaz de planificar esta ejecución en pasos discretos.17

**Algoritmo de Ejecución para el Agente:**

1. **Identificación de Activos:** Seleccionar una funcionalidad específica del monolito para extraer (ej. "Gestión de Nóminas").  
2. **Inyección de Proxy (Intercepción):** Colocar una capa de interceptación HTTP (API Gateway o Proxy Inverso como NGINX) frente al monolito. Inicialmente, el 100% del tráfico pasa al monolito.  
3. **Implementación Paralela:** Construir el nuevo microservicio de "Nóminas" con la nueva tecnología y lógica.  
4. **Desvío de Tráfico (Switch-Over):** Reconfigurar el proxy para desviar las llamadas de /payroll al nuevo servicio, mientras el resto del tráfico sigue yendo al monolito.  
   * *Nota Crítica:* Esto permite revertir el cambio instantáneamente (reconfigurando el proxy) si el nuevo servicio falla.  
5. **Estrangulamiento:** Repetir el proceso funcionalidad por funcionalidad hasta que el monolito sea irrelevante y pueda ser decomisado.

Variante: Captura de Activos (Asset Capture)  
El Agente debe reconocer que a veces no se puede interceptar el tráfico fácilmente. En estos casos, el patrón implica identificar qué datos o activos posee el monolito y mover sistemáticamente la autoridad de esos datos al nuevo servicio.

### **3.2 Patrón Branch by Abstraction (Rama por Abstracción)**

Cuando la intercepción HTTP no es posible (ej. código profundo dentro de una aplicación monolítica), el Agente debe recomendar **Branch by Abstraction**.20

1. Crear una abstracción (interfaz) dentro del código del monolito para la funcionalidad a reemplazar.  
2. Mover el código existente detrás de una implementación de esta interfaz.  
3. Crear una segunda implementación que llame al nuevo microservicio.  
4. Utilizar un "Feature Toggle" (interruptor de funcionalidad) para cambiar entre la vieja y la nueva implementación en tiempo de ejecución.

Esta técnica permite que el código nuevo y viejo coexistan en el mismo despliegue, facilitando pruebas A/B y retrocesos rápidos.20

## ---

**Parte IV: Arquitectura de Datos \- El Problema Más Difícil**

Newman enfatiza que los datos son la parte más difícil de los microservicios. En un monolito, la base de datos es el integrador. En microservicios, compartir la base de datos es un pecado capital (Acoplamiento Común). El Agente debe aplicar estrictamente la **Soberanía de Datos**.

### **4.1 Patrones de Descomposición de Base de Datos**

Cuando el Agente se enfrenta a un monolito con una base de datos gigante y compartida, debe seleccionar el patrón de separación adecuado para evitar el caos.

#### **4.1.1 Patrón: Database View (Vista de Base de Datos)**

* **Escenario:** El Servicio B necesita datos del Servicio A, pero no queremos que acceda a las tablas directamente para evitar acoplamiento a cambios de esquema.  
* **Solución:** Crear una Vista SQL en la base de datos de A que proyecte solo los datos necesarios para B. El Servicio B tiene permiso de lectura sobre esa Vista, no sobre las tablas.21  
* **Veredicto del Agente:** Útil como paso intermedio. Proporciona cierto ocultamiento de información, pero mantiene el acoplamiento físico a la misma instancia de base de datos (riesgo de contención de recursos).

#### **4.1.2 Patrón: Database Wrapping Service (Servicio Envoltorio)**

* **Escenario:** El esquema de la base de datos es demasiado complejo para dividirse, o muchas aplicaciones acceden a ella.  
* **Solución:** Crear un servicio delgado que "envuelva" la base de datos. Mover todas las consultas SQL de los clientes a este servicio, exponiéndolas como métodos API.22  
* **Veredicto del Agente:** Excelente para establecer límites de propiedad claros. Convierte dependencias de base de datos en dependencias de servicio. Permite controlar la lógica de escritura. Es un precursor necesario para la separación física futura.

#### **4.1.3 Patrón: Database-as-a-Service Interface (Interfaz de Base de Datos como Servicio)**

* **Escenario:** Un cliente (ej. una herramienta de reportes o BI) necesita acceso SQL masivo para realizar consultas complejas ad-hoc, lo cual es ineficiente a través de una API REST.  
* **Solución:** Crear una base de datos de lectura dedicada para este cliente. Usar un motor de mapeo (o Change Data Capture \- CDC) para replicar y transformar los datos desde la base de datos interna del microservicio hacia esta base de datos externa.20  
* **Diferencia Clave:** A diferencia del "Wrapping Service" (que es una API), aquí se expone un *endpoint SQL* real, pero sobre una base de datos de solo lectura desacoplada de la transaccional.  
* **Veredicto del Agente:** Ideal para reportes y análisis. Protege la base de datos transaccional de consultas pesadas y permite cambiar el esquema interno sin romper los reportes externos.

### **4.2 Separación Lógica vs. Física**

El Agente debe distinguir entre estos dos estados.11

* **Separación Lógica:** Usar esquemas diferentes (CREATE SCHEMA billing) dentro del mismo servidor de base de datos. Es un buen primer paso para verificar que el código está desacoplado.  
* **Separación Física:** Servidores de base de datos totalmente distintos. Es el objetivo final para garantizar aislamiento total de fallos y rendimiento (bulkheading), aunque incrementa la complejidad operativa.

## ---

**Parte V: Coherencia de Datos y Transacciones Distribuidas**

El Agente debe aceptar una verdad incómoda: en sistemas distribuidos, no podemos confiar en transacciones ACID distribuidas. El Teorema CAP impone restricciones físicas. Newman aconseja encarecidamente **evitar las transacciones distribuidas como Two-Phase Commit (2PC)**.26

### **5.1 El Rechazo a Two-Phase Commit (2PC)**

El protocolo 2PC requiere un coordinador que bloquea recursos en todos los participantes hasta que todos confirman.

* **Heurística de Rechazo:**  
  1. **Latencia:** 2PC es bloqueante; la latencia es la del nodo más lento.  
  2. **Disponibilidad:** Si el coordinador falla, el sistema se detiene.  
  3. **Soporte:** Muchas bases de datos modernas (NoSQL) no lo soportan.  
  * *Conclusión del Agente:* Evitar 2PC a toda costa en arquitecturas de microservicios.26

### **5.2 Sagas: La Alternativa de Consistencia Eventual**

El marco de decisión del Agente debe favorecer el patrón **Saga**. Una Saga es una secuencia de transacciones locales. Si una falla, se ejecutan **Transacciones Compensatorias** para deshacer los cambios previos.26

Matriz de Decisión: Orquestación vs. Coreografía  
Dentro de las Sagas, el Agente debe elegir entre dos estilos de implementación. Esta es una decisión arquitectónica crítica.27  
**Tabla 5.1: Matriz de Decisión Saga**

| Característica | Coreografía (Event-Driven) | Orquestación (Command-Driven) |
| :---- | :---- | :---- |
| **Mecanismo** | Los servicios reaccionan a eventos de dominio. Sin coordinador central. | Un servicio central (Orquestador) dice a los participantes qué hacer. |
| **Flujo** | Servicio A emite "Evento Creado" \-\> Servicio B escucha y actúa. | Orquestador llama a A, espera respuesta, luego llama a B. |
| **Acoplamiento** | **Bajo**. El emisor no conoce a los receptores. | **Más Alto**. El orquestador conoce a todos los participantes. |
| **Visibilidad** | Baja. Difícil rastrear el flujo completo mentalmente. | Alta. El flujo está definido en un lugar central. |
| **Escenario Ideal** | Flujos simples, pocos pasos, necesidad de alta extensibilidad. | Flujos complejos, muchas ramas de decisión, necesidad de control estricto. |
| **Riesgo** | "Infierno de Eventos". Ciclos de dependencia invisibles. | "Servicio Dios". El orquestador acumula demasiada lógica de negocio. |

**Escenario Simulado de Entrenamiento:**

* *Caso:* Un proceso de "Reserva de Viajes" que incluye Vuelo, Hotel y Coche.  
* *Condición:* El flujo tiene reglas complejas (ej. "Si el Hotel falla, intenta buscar otro en 5km a la redonda antes de cancelar el Vuelo").  
* *Decisión del Agente:* **Orquestación**. La lógica de recuperación compleja y las decisiones condicionales son difíciles de implementar en Coreografía pura sin esparcir la lógica de negocio. Un Orquestador centralizado (quizás usando un motor como Camunda o AWS Step Functions) es superior aquí.

## ---

**Parte VI: Estilos de Comunicación e Integración**

El Agente debe seleccionar no solo la tecnología (REST, gRPC), sino el estilo de colaboración. Newman distingue entre tecnología y estilo.4

### **6.1 Síncrono vs. Asíncrono**

* **Síncrono (Blocking):** El cliente espera respuesta. (HTTP/REST).  
  * *Riesgo:* Acoplamiento temporal. Si el servicio destino cae, el origen falla o se bloquea.  
* **Asíncrono (Non-Blocking):** El cliente envía y olvida o espera callback. (RabbitMQ, Kafka).  
  * *Ventaja:* Desacoplamiento temporal. Permite manejar picos de carga (load levelling).

### **6.2 Request-Response vs. Event-Driven**

Newman aconseja: "Prefiere poner en un evento lo que estarías feliz de compartir vía una API".10

* **Smart Endpoints, Dumb Pipes:** El Agente debe evitar poner lógica de negocio en el middleware (como en los antiguos ESB). La inteligencia debe estar en los servicios (endpoints), y la tubería (broker de mensajes) debe ser simple transporte.10

### **6.3 Tecnología de Interfaz**

* **REST sobre HTTP:** Estándar, fácil, pero verboso.  
* **gRPC:** Alto rendimiento, tipado fuerte, ideal para comunicación interna servicio-a-servicio.28  
* **GraphQL:** Permite a los clientes pedir exactamente lo que necesitan. Reduce el "over-fetching", pero acopla el backend a las necesidades de presentación del frontend.

## ---

**Parte VII: Complejidad Operativa y Observabilidad**

El movimiento hacia microservicios rompe las herramientas de monitoreo tradicionales. El Agente debe exigir una estrategia de **Observabilidad** basada en tres pilares para aprobar una arquitectura.11

### **7.1 Agregación de Logs y Métricas**

Con 50 servicios, no se puede hacer SSH a un servidor para ver logs. Los logs deben fluir a un sistema centralizado (ELK, Splunk). Las métricas deben ser agregadas para ver tendencias de latencia y error.

### **7.2 Trazabilidad Distribuida (Distributed Tracing)**

Este es el requisito más crítico en la fase de operación.

* **Correlation IDs:** El Agente debe imponer que *cada* solicitud que entra al sistema reciba un ID de Correlación único. Este ID debe propagarse en las cabeceras de todas las llamadas subsiguientes entre microservicios.  
* **Utilidad:** Sin esto, depurar un error 500 que ocurre cinco saltos de servicio adentro es imposible. El Agente debe considerar la falta de Correlation IDs como un defecto de calidad bloqueante.31

### **7.3 Resiliencia: Circuit Breakers y Bulkheads**

El sistema fallará. El Agente debe diseñar para el fallo.

* **Circuit Breaker:** Si un servicio detecta que su dependencia está fallando repetidamente, debe "abrir el circuito" y dejar de llamar inmediatamente, devolviendo un error o una respuesta por defecto. Esto evita el agotamiento de recursos (hilos, conexiones) esperando a un servicio muerto.  
* **Bulkheads (Mamparos):** Aislar recursos (ej. pools de hilos separados para diferentes clientes o servicios). Si el componente de "Procesamiento de Imágenes" consume toda la CPU, no debe tirar abajo el componente de "Login".

## ---

**Parte VIII: Alineación Organizacional y la Ley de Conway**

Newman dedica una parte sustancial a la sociología del software. El Agente debe entender que la arquitectura técnica y la estructura organizacional son isomorfas.

### **8.1 La Ley de Conway**

"Cualquier organización que diseña un sistema... producirá un diseño cuya estructura es una copia de la estructura de comunicación de la organización." — Melvin Conway.32

Si tienes un equipo de DBAs, un equipo de Frontend y un equipo de Backend separados, inevitablemente producirás una arquitectura en capas, no microservicios.

### **8.2 La Maniobra Inversa de Conway (Inverse Conway Maneuver)**

El Agente debe recomendar cambios organizacionales para lograr la arquitectura deseada.33

* **Estrategia:** Para lograr microservicios desacoplados, la organización debe estructurarse en equipos pequeños, multifuncionales y autónomos que posean un servicio de extremo a extremo (desde la UI hasta la base de datos).  
* **Tamaño del Equipo:** Aplicar la regla de "Two Pizza Team" (equipos que pueden alimentarse con dos pizzas). Equipos pequeños poseen servicios pequeños. Si el equipo crece demasiado, el servicio probablemente es demasiado grande y debe dividirse.34

## ---

**Parte IX: Marcos de Decisión Sintetizados para el Agente**

Para concluir, se presentan las tablas maestras de decisión que el Agente debe consultar ante dilemas arquitectónicos.

**Tabla 9.1: Heurística Maestra de Adopción de Microservicios**

| Factor | Condición para Monolito | Condición para Microservicios |
| :---- | :---- | :---- |
| **Comprensión del Dominio** | Baja / Nuevo Negocio | Alta / Dominio Maduro |
| **Tamaño del Equipo** | \< 10 Desarrolladores | \> 50 Desarrolladores |
| **Necesidad de Escala** | Uniforme | Partes específicas necesitan escalar independientemente |
| **Frecuencia de Despliegue** | Semanal / Mensual | Múltiples veces al día por equipo |
| **Tolerancia a Fallos** | Baja (Simplicidad preferida) | Alta (Aislamiento de fallos requerido) |

**Tabla 9.2: Estrategia de Migración de Datos**

| Escenario | Patrón Recomendado |
| :---- | :---- |
| **Lectura de datos de otro servicio** | Usar API del servicio propietario (Domain Coupling). |
| **Reportes masivos / BI** | **Database-as-a-Service Interface** con replicación asíncrona. |
| **Migración de esquema complejo** | **Database Wrapping Service** como paso intermedio. |
| **Compartir tablas mutables** | **PROHIBIDO**. Re-arquitecturar inmediatamente. |

Conclusión Final  
El Agente entrenado con este informe no es un promotor ciego de los microservicios, sino un guardián de la complejidad. Su función es cuestionar la necesidad de distribución, forzar la claridad en los límites del dominio (DDD), asegurar la independencia de despliegue y gestionar la consistencia de datos a través de patrones asíncronos robustos. En la visión de Sam Newman, el éxito no es tener microservicios; el éxito es entregar valor de negocio de manera sostenible, y la arquitectura es solo una herramienta para ese fin.

---

**Citations:** 1

#### **Obras citadas**

1. Microservice Trade-Offs \- Martin Fowler, fecha de acceso: enero 12, 2026, [https://martinfowler.com/articles/microservice-trade-offs.html](https://martinfowler.com/articles/microservice-trade-offs.html)  
2. Microservices Architecture for eCommerce \- Studylib, fecha de acceso: enero 12, 2026, [https://studylib.net/doc/27650123/microservices-architecture-for-ecommerce](https://studylib.net/doc/27650123/microservices-architecture-for-ecommerce)  
3. Microservice Premium \- Martin Fowler, fecha de acceso: enero 12, 2026, [https://martinfowler.com/bliki/MicroservicePremium.html](https://martinfowler.com/bliki/MicroservicePremium.html)  
4. Building Microservices, 2nd Edition \- Sam Newman, fecha de acceso: enero 12, 2026, [https://samnewman.io/books/building\_microservices\_2nd\_edition/](https://samnewman.io/books/building_microservices_2nd_edition/)  
5. Book summary: Building Microservices (2nd Edition) \- Blog \- dornea.nu, fecha de acceso: enero 12, 2026, [https://blog.dornea.nu/2022/08/10/book-summary-building-microservices-2nd-edition/](https://blog.dornea.nu/2022/08/10/book-summary-building-microservices-2nd-edition/)  
6. Book notes: Monolith to Microservices: Evolutionary Patterns to Transform Your Monolith \- Daniel Lebrero, fecha de acceso: enero 12, 2026, [https://danlebrero.com/2022/02/09/monolith-to-microservices-summary/](https://danlebrero.com/2022/02/09/monolith-to-microservices-summary/)  
7. Quotes by Sam Newman (Author of Building Microservices) \- Goodreads, fecha de acceso: enero 12, 2026, [https://www.goodreads.com/author/quotes/3362774.Sam\_Newman](https://www.goodreads.com/author/quotes/3362774.Sam_Newman)  
8. How to request information from multiple microservices? \- Enterprise Craftsmanship, fecha de acceso: enero 12, 2026, [https://enterprisecraftsmanship.com/posts/how-to-request-information-from-multiple-microservices/](https://enterprisecraftsmanship.com/posts/how-to-request-information-from-multiple-microservices/)  
9. a good book that covers modular monoliths and transitioning modules to microservices? : r/dotnet \- Reddit, fecha de acceso: enero 12, 2026, [https://www.reddit.com/r/dotnet/comments/ylqu7k/a\_good\_book\_that\_covers\_modular\_monoliths\_and/](https://www.reddit.com/r/dotnet/comments/ylqu7k/a_good_book_that_covers_modular_monoliths_and/)  
10. Book notes: Building Microservices \- Second edition \- Daniel Lebrero, fecha de acceso: enero 12, 2026, [https://danlebrero.com/2023/01/24/building-microservices-second-edition-designing-fine-grained-systems-summary/](https://danlebrero.com/2023/01/24/building-microservices-second-edition-designing-fine-grained-systems-summary/)  
11. Building Microservices: Designing Fine-Grained Systems \[2 ed.\] 1492034029, 9781492034025 \- DOKUMEN.PUB, fecha de acceso: enero 12, 2026, [https://dokumen.pub/building-microservices-designing-fine-grained-systems-2nbsped-1492034029-9781492034025.html](https://dokumen.pub/building-microservices-designing-fine-grained-systems-2nbsped-1492034029-9781492034025.html)  
12. How Coupled Are Your Microservices? \- JAVAPRO International, fecha de acceso: enero 12, 2026, [https://javapro.io/2025/11/04/how-coupled-are-your-microservices/](https://javapro.io/2025/11/04/how-coupled-are-your-microservices/)  
13. Microservices 101 ft. DDD: The good, the bad & the ugly. \- Karam.io, fecha de acceso: enero 12, 2026, [https://www.karam.io/blog/2019/microservices-101-ft-ddd-the-good-the-bad-and-the-ugly/](https://www.karam.io/blog/2019/microservices-101-ft-ddd-the-good-the-bad-and-the-ugly/)  
14. Book review : Building Microservices | by Senthil Kumar \- Medium, fecha de acceso: enero 12, 2026, [https://medium.com/@senthilnow/book-review-building-microservices-a4687f9b3e01](https://medium.com/@senthilnow/book-review-building-microservices-a4687f9b3e01)  
15. building microservices \- Thoughtworks, fecha de acceso: enero 12, 2026, [https://www.thoughtworks.com/content/dam/thoughtworks/documents/books/bk\_building-microservices-chapter-5\_en.pdf](https://www.thoughtworks.com/content/dam/thoughtworks/documents/books/bk_building-microservices-chapter-5_en.pdf)  
16. kboom/awesome-quotes: The collection of short quotes relevant to software engineering. \- GitHub, fecha de acceso: enero 12, 2026, [https://github.com/kboom/awesome-quotes](https://github.com/kboom/awesome-quotes)  
17. Using the Strangler Fig Pattern on a monolithic game server \- Squarespace, fecha de acceso: enero 12, 2026, [https://static1.squarespace.com/static/6082f965d1814c6616e0988b/t/6669713c933cc067ca3dbd77/1718186301057/strangler\_paper.pdf](https://static1.squarespace.com/static/6082f965d1814c6616e0988b/t/6669713c933cc067ca3dbd77/1718186301057/strangler_paper.pdf)  
18. Existing resources | Distributed Application Architecture Patterns, fecha de acceso: enero 12, 2026, [https://jurf.github.io/daap/methodology/existing-resources/](https://jurf.github.io/daap/methodology/existing-resources/)  
19. Podcast | Microservices as a last resort with Sam Newman \- Toro Cloud \- Lonti, fecha de acceso: enero 12, 2026, [https://www.lonti.com/podcast/microservices-last-resort-sam-newman](https://www.lonti.com/podcast/microservices-last-resort-sam-newman)  
20. Monolith to Microservices, fecha de acceso: enero 12, 2026, [http://103.203.175.90:81/fdScript/RootOfEBooks/E%20Book%20collection%20-%202023%20-%20G/CSE%20%20IT%20AIDS%20ML/Monolith-to-Microservices.pdf](http://103.203.175.90:81/fdScript/RootOfEBooks/E%20Book%20collection%20-%202023%20-%20G/CSE%20%20IT%20AIDS%20ML/Monolith-to-Microservices.pdf)  
21. SaraLerma/Monolith-To-Microservices \- GitHub, fecha de acceso: enero 12, 2026, [https://github.com/SaraLerma/Monolith-To-Microservices](https://github.com/SaraLerma/Monolith-To-Microservices)  
22. Notes: Monolith to Microservices by Sam Newman \- Edd Mann, fecha de acceso: enero 12, 2026, [https://eddmann.com/posts/notes-monolith-to-microservices-by-sam-newman/](https://eddmann.com/posts/notes-monolith-to-microservices-by-sam-newman/)  
23. From Monolith to Microservices: Refactoring Patterns \- IS MUNI, fecha de acceso: enero 12, 2026, [https://is.muni.cz/th/f8zv4/Master\_Thesis.pdf](https://is.muni.cz/th/f8zv4/Master_Thesis.pdf)  
24. Monolith to Microservices. Evolutionary Patterns to Transform Your Monolith Sam Newman \- Helion, fecha de acceso: enero 12, 2026, [https://helion.pl/ksiazki/monolith-to-microservices-evolutionary-patterns-to-transform-your-monolith-sam-newman,e\_1e27.htm](https://helion.pl/ksiazki/monolith-to-microservices-evolutionary-patterns-to-transform-your-monolith-sam-newman,e_1e27.htm)  
25. Building Microservices, fecha de acceso: enero 12, 2026, [https://api.pageplace.de/preview/DT0400.9781492033998\_A49444743/preview-9781492033998\_A49444743.pdf](https://api.pageplace.de/preview/DT0400.9781492033998_A49444743/preview-9781492033998_A49444743.pdf)  
26. Sagas: An Alternative for Data Consistency in Microservices – Software Engineering, fecha de acceso: enero 12, 2026, [https://softengbook.org/articles/sagas](https://softengbook.org/articles/sagas)  
27. Microservices Pattern: Distributed Transactions (SAGA) | by Joud W. Awad | Medium, fecha de acceso: enero 12, 2026, [https://medium.com/@joudwawad/microservices-pattern-distributed-transactions-saga-92b5e933cea1](https://medium.com/@joudwawad/microservices-pattern-distributed-transactions-saga-92b5e933cea1)  
28. Immersive guide to microservices \- Level Up Coding, fecha de acceso: enero 12, 2026, [https://levelup.gitconnected.com/immersive-guide-to-microservices-f646a691d219](https://levelup.gitconnected.com/immersive-guide-to-microservices-f646a691d219)  
29. Orchestration or Choreography? \- Transforming Leadership \- WordPress.com, fecha de acceso: enero 12, 2026, [https://edwardthienhoang.wordpress.com/2018/08/08/orchestration-or-choreography/](https://edwardthienhoang.wordpress.com/2018/08/08/orchestration-or-choreography/)  
30. Orchestrator Vs Choreography for Microservices | by 15Y6C34 NG JUN GUANG JARROD, fecha de acceso: enero 12, 2026, [https://medium.com/@ng.junguang.jarrod/orchestrator-vs-choreography-for-microservices-45f6c6503927](https://medium.com/@ng.junguang.jarrod/orchestrator-vs-choreography-for-microservices-45f6c6503927)  
31. Leveraging Correlation IDs to Increase Backend System Observability \- Medium, fecha de acceso: enero 12, 2026, [https://medium.com/insiderengineering/leveraging-correlation-ids-to-increase-backend-system-observability-daa2fb0f0438](https://medium.com/insiderengineering/leveraging-correlation-ids-to-increase-backend-system-observability-daa2fb0f0438)  
32. Microservices \- Martin Fowler, fecha de acceso: enero 12, 2026, [https://martinfowler.com/articles/microservices.html](https://martinfowler.com/articles/microservices.html)  
33. Conway's Law and Intentional Design \- Sergio Caredda, fecha de acceso: enero 12, 2026, [https://sergiocaredda.eu/organisation/conways-law-and-intentional-design](https://sergiocaredda.eu/organisation/conways-law-and-intentional-design)  
34. Book Report \- Building Microservices \- Jordan Robinson, fecha de acceso: enero 12, 2026, [https://blog.jordanrobinson.co.uk/building-microservices](https://blog.jordanrobinson.co.uk/building-microservices)  
35. Monolith to Microservices \- F5, fecha de acceso: enero 12, 2026, [https://cdn.studio.f5.com/files/k6fem79d/production/1b3b4a1fa7330b388639d054991ca221998b50b0.pdf](https://cdn.studio.f5.com/files/k6fem79d/production/1b3b4a1fa7330b388639d054991ca221998b50b0.pdf)