# **Manual Superior de Arquitectura de Sistemas Intensivos en Datos: Frameworks de Decisión, Heurísticas y Análisis de Trade-offs**

### **Una Síntesis Operativa de "Designing Data-Intensive Applications" para la Instrucción de Agentes de IA**

## ---

**1\. Introducción: La Nueva Realidad de la Ingeniería de Software**

En las últimas dos décadas, hemos sido testigos de un cambio tectónico en la naturaleza fundamental de los sistemas de software. Mientras que históricamente el cuello de botella residía en la capacidad de cómputo —ciclos de CPU limitados para resolver algoritmos complejos—, la arquitectura moderna se enfrenta predominantemente a desafíos derivados de la cantidad, la complejidad y la velocidad de los datos. Hemos transitado de una era *compute-intensive* a una era *data-intensive*. Para un Agente de Inteligencia Artificial encargado de diseñar o mantener tales sistemas, esta distinción no es semántica, sino operativa: las restricciones físicas ya no son solo la velocidad del procesador, sino el ancho de banda de la red, la latencia de disco y la coherencia de la información distribuida.1

Este reporte sintetiza el cuerpo de conocimiento presentado por Martin Kleppmann en *Designing Data-Intensive Applications* (DDIA), estructurándolo no como un resumen literario, sino como un conjunto de frameworks de decisión arquitectónica. El objetivo es dotar al Agente de la capacidad para navegar el vasto panorama de herramientas (SQL, NoSQL, NewSQL, Streaming, Batch) no a través de modas o "buzzwords", sino mediante un análisis riguroso de los compromisos (trade-offs) inherentes a cada elección de diseño.4

### **1.1. La Tríada Axiomática del Diseño de Sistemas**

Para evaluar la viabilidad de cualquier arquitectura propuesta, el Agente debe interiorizar tres preocupaciones fundamentales que actúan como las dimensiones rectoras del espacio de diseño. Estas no son características opcionales, sino requisitos no funcionales que determinan la supervivencia del sistema a largo plazo.6

#### **1.1.1. Fiabilidad (Reliability): La Resiliencia ante lo Inevitable**

La fiabilidad se define como la capacidad de un sistema para continuar operando correctamente —realizando su función deseada al nivel de rendimiento esperado— incluso ante la presencia de adversidades, denominadas técnicamente "fallos" (*faults*). El Agente debe distinguir ontológicamente entre *fault* (fallo de un componente) y *failure* (insuficiencia del sistema).

El principio rector aquí es el reconocimiento de que los fallos son inevitables. A medida que un sistema escala horizontalmente, la probabilidad de que todos los componentes (hardware, red, procesos) funcionen correctamente en un instante dado tiende a cero.9 Por lo tanto, la heurística de decisión no debe ser "prevenir fallos", sino "tolerar fallos". Un diseño fiable es aquel que impide que un *fault* local escale hasta convertirse en un *failure* global.

Las categorías de fallos que el Agente debe modelar incluyen:

* **Fallos de Hardware:** Discos que mueren, cortes de energía. La respuesta estándar es la redundancia de hardware (RAID, dual-power paths) y, en sistemas distribuidos, la replicación de software, permitiendo que la pérdida de un nodo sea transparente para el usuario final.  
* **Fallos de Software:** Errores sistemáticos, difíciles de predecir porque suelen estar correlacionados. Un bug en el kernel de Linux o en el recolector de basura de Java puede tumbar todas las réplicas simultáneamente si se exponen al mismo input desencadenante. La defensa aquí es la simplicidad, el aislamiento de procesos y el reinicio rápido.  
* **Errores Humanos:** La causa principal de incidentes. La arquitectura debe desacoplar los entornos, permitir *rollbacks* rápidos y exponer interfaces que hagan "fácil hacer lo correcto y difícil hacer lo incorrecto".9

#### **1.1.2. Escalabilidad (Scalability): La Gestión Matemática del Crecimiento**

La escalabilidad no es una etiqueta estática que se aplica a un sistema, sino una función que describe la capacidad del sistema para manejar una carga creciente. Para el Agente, la pregunta clave no es "¿es escalable?", sino "¿si duplicamos la carga, cuántos recursos adicionales necesitamos para mantener el rendimiento?".7

El primer paso para cualquier análisis de escalabilidad es definir los **Parámetros de Carga**. Estos varían drásticamente según el dominio:

* En un servidor web, pueden ser peticiones por segundo.  
* En una base de datos, la proporción de lecturas frente a escrituras.  
* En un sistema de chat, el número de usuarios activos concurrentes.

El Agente debe ser entrenado para identificar los "puntos de inflexión" donde una arquitectura deja de ser lineal. Un caso de estudio canónico analizado por Kleppmann es la evolución de la arquitectura de Twitter.3

Escenario Simulado: El Problema del Fan-out en Redes Sociales  
El desafío de escalabilidad de Twitter no es el almacenamiento de tweets, sino la entrega de los mismos a los seguidores (fan-out).

* **Enfoque 1 (Pull/Global Collection):** Cuando un usuario tuitea, se inserta en una tabla global. Cuando un usuario ve su timeline, el sistema ejecuta una consulta SQL compleja (SELECT \* FROM tweets WHERE sender\_id IN (mis\_seguidores)).  
  * *Análisis de Trade-off:* Escritura barata y rápida. Lectura computacionalmente costosa. A medida que aumenta el número de usuarios, la latencia de lectura se degrada inaceptablemente.  
* **Enfoque 2 (Push/Fan-out on Write):** Cada usuario tiene una lista pre-calculada (cache) de su timeline. Cuando alguien tuitea, el sistema busca a todos sus seguidores e inserta el tweet en sus listas individuales.  
  * *Análisis de Trade-off:* Lectura instantánea (O(1)). Escritura costosa y variable. Para usuarios con pocos seguidores, es eficiente. Para celebridades con 100 millones de seguidores, un solo tweet genera 100 millones de escrituras, causando un pico de latencia masivo ("The Justin Bieber problem").  
* **Decisión Híbrida:** El Agente debe reconocer que la solución óptima suele ser híbrida. Usar *Push* para la mayoría de usuarios, pero *Pull* para celebridades, combinando los resultados en tiempo de lectura.12

#### **1.1.3. Mantenibilidad (Maintainability): La Economía del Software**

La mantenibilidad aborda el hecho económico de que el mayor costo del software no es su desarrollo inicial, sino su operación y evolución continua. Kleppmann desglosa esto en tres pilares para el Agente 6:

1. **Operabilidad:** Visibilidad, monitoreo y herramientas para que el equipo de operaciones pueda intervenir ante anomalías.  
2. **Simplicidad:** La reducción de la complejidad. Aquí es crucial distinguir entre *Complejidad Esencial* (inherente al problema del dominio) y *Complejidad Accidental* (introducida por la implementación). El Agente debe priorizar abstracciones que eliminen la complejidad accidental.15  
3. **Evolubilidad:** La facilidad para adaptar el sistema a requisitos futuros no previstos, a menudo mediante la flexibilidad en el esquema de datos.

## ---

**2\. Modelos de Datos: La Estructura del Pensamiento Arquitectónico**

La elección del modelo de datos es posiblemente la decisión más consecuente en el diseño de una aplicación, ya que impone límites sobre cómo los ingenieros piensan y manipulan la información. El Agente debe navegar más allá de la falsa dicotomía "SQL vs. NoSQL" y entender las topologías de datos subyacentes.1

### **2.1. El Modelo Relacional vs. Documental: La Batalla por la Localidad**

Históricamente, el modelo relacional dominó por su rigor matemático y su capacidad para normalizar datos, reduciendo la redundancia. Sin embargo, el auge del modelo documental (JSON/BSON) responde a una necesidad pragmática: la **Localidad de Datos**.

#### **Framework de Decisión: Relacional vs. Documental**

Para elegir entre estos modelos, el Agente debe analizar la estructura de acceso a los datos:

* **El Argumento Documental:** Si los datos tienen una estructura inherente de árbol (uno-a-muchos) y la aplicación típicamente accede al árbol completo a la vez (por ejemplo, cargar un perfil de usuario que incluye historial laboral, educación y contacto), el modelo documental es superior. Permite recuperar toda la información en una sola operación de lectura secuencial, evitando la fragmentación y la sobrecarga de múltiples accesos a disco.1  
  * *Trade-off:* El soporte para uniones (*joins*) es débil o inexistente. Si los datos están altamente normalizados y requieren cruces constantes, la lógica debe trasladarse al código de la aplicación, lo que aumenta la complejidad y la latencia de red.  
* **El Argumento Relacional:** Si los datos están altamente interconectados (muchos-a-muchos) y no existe una jerarquía clara, el modelo relacional brilla. Su fortaleza reside en el *Query Optimizer*, que decide dinámicamente el mejor camino para ejecutar una consulta compleja.  
  * *Trade-off:* Sufre del "Impedance Mismatch" (Desajuste de Impedancia). Los objetos en la memoria de la aplicación (grafos de objetos) deben ser descompuestos (*shredded*) en tablas planas para el almacenamiento, requiriendo una capa de traducción (ORM) que a menudo introduce ineficiencias de rendimiento.

### **2.2. El Modelo de Grafos: Priorizando las Relaciones**

Cuando las relaciones entre los datos son tan importantes o más que los datos mismos, tanto el modelo relacional como el documental se quiebran. En un escenario de detección de fraude o análisis de redes sociales, intentar recorrer conexiones de múltiples saltos en SQL resulta en consultas recursivas exponencialmente lentas.

El modelo de grafos (e.g., Neo4j, Property Graphs) trata a los vértices y las aristas como ciudadanos de primera clase. La heurística clave aquí es que el costo de recorrer una relación en un grafo es constante ($O(1)$) e independiente del tamaño total de la base de datos, a diferencia de los índices relacionales que suelen tener un costo logarítmico ($O(\\log N)$).1

**Tabla de Decisión de Modelos de Datos**

| Característica del Dominio | Modelo Recomendado | Justificación Técnica |
| :---- | :---- | :---- |
| **Estructura de Árbol / Jerárquica** | Documental (JSON) | Maximiza localidad de datos; evita joins innecesarios. |
| **Reportes Analíticos / Joins Complejos** | Relacional (SQL) | Optimización de consultas madura; integridad referencial fuerte. |
| **Redes Complejas / Muchos-a-Muchos** | Grafos (Property Graph) | Travesía de relaciones en tiempo constante; flexibilidad de esquema. |
| **Esquema Volátil / Heterogéneo** | Documental | Schema-on-Read permite polimorfismo de datos sin migraciones. |

## ---

**3\. Motores de Almacenamiento: La Mecánica de la Persistencia**

Debajo de la interfaz SQL o API, la base de datos debe gestionar bytes en disco. El Agente debe comprender las dos familias principales de motores de almacenamiento para predecir el rendimiento de lectura/escritura: los motores basados en **Log-Structured Merge-Trees (LSM)** y los basados en **B-Trees**.14

### **3.1. Log-Structured Merge-Trees (LSM-Trees)**

Utilizados en sistemas modernos de alto rendimiento de escritura como Cassandra, RocksDB, LevelDB e InfluxDB.

* **Mecanismo:** La idea central es que escribir secuencialmente en disco es órdenes de magnitud más rápido que la escritura aleatoria.  
  1. Las escrituras se agregan a un búfer en memoria ordenado (Memtable, usualmente un árbol Rojo-Negro).  
  2. Cuando el Memtable se llena, se vuelca a disco como un archivo inmutable ordenado (**SSTable** \- Sorted String Table).  
  3. Las lecturas buscan primero en el Memtable, luego en el SSTable más reciente, y así sucesivamente hacia atrás.  
  4. Un proceso de fondo (**Compaction**) fusiona SSTables antiguos, descartando valores sobrescritos o eliminados.  
* **Trade-offs Críticos:**  
  * *Ventaja:* **Throughput de Escritura Superior**. Al transformar todas las operaciones en escrituras secuenciales, minimiza el movimiento del cabezal en HDDs y reduce la amplificación de escritura en SSDs.  
  * *Desventaja:* **Amplificación de Lectura**. Leer un dato inexistente puede requerir verificar todos los SSTables. (Se mitiga usando Filtros de Bloom). La latencia de lectura puede ser variable debido a la contención de recursos durante la compactación.

### **3.2. B-Trees**

El estándar de la industria durante 40 años, utilizado en PostgreSQL, MySQL, Oracle y SQL Server.

* **Mecanismo:** Divide la base de datos en páginas de tamaño fijo (típicamente 4KB o 8KB). Estas páginas son las unidades de lectura y escritura. Las páginas se organizan en un árbol balanceado amplio. Las actualizaciones se realizan *in-place* (sobrescribiendo la página existente en disco).  
* **Trade-offs Críticos:**  
  * *Ventaja:* **Rendimiento de Lectura Predecible**. Encontrar una clave requiere un número fijo y bajo de saltos. Excelente para consultas de rango.  
  * *Desventaja:* **Amplificación de Escritura**. Modificar un solo byte requiere leer, modificar y reescribir toda la página de 4KB. Además, requiere un *Write-Ahead Log* (WAL) para recuperación de fallos, duplicando efectivamente la escritura. Las escrituras aleatorias son penalizadas fuertemente por el hardware de disco.

**Heurística de Entrenamiento para el Agente:**

*Si el perfil de carga es predominantemente de escritura (Write-Heavy) o requiere ingestión masiva de eventos (IoT, Logs): **Seleccionar LSM-Tree**. Si el perfil requiere lecturas complejas, transaccionalidad fuerte y latencias muy estables: **Seleccionar B-Tree**.*

## ---

**4\. Codificación y Evolución: El Lenguaje del Cambio**

En sistemas distribuidos de larga duración, el cambio es la única constante. Kleppmann acuña la frase crítica: *"Data outlives code"* (Los datos sobreviven al código). Mientras que el código se actualiza frecuentemente, los datos en la base de datos pueden haber sido escritos hace años. El Agente debe gestionar la compatibilidad a través de la evolución del esquema.14

### **4.1. Compatibilidad Bidireccional**

Para permitir despliegues sin tiempo de inactividad (*rolling upgrades*), el sistema debe soportar:

1. **Compatibilidad hacia atrás (Backward Compatibility):** El código nuevo debe poder leer datos escritos por código antiguo.  
2. **Compatibilidad hacia adelante (Forward Compatibility):** El código antiguo debe poder leer datos escritos por código nuevo (ignorando los campos nuevos que no conoce).

### **4.2. Formatos de Serialización**

* **Texto (JSON/XML):** Ofrecen conveniencia y legibilidad humana, pero son verbosos y carecen de esquema explícito, delegando la validación a la aplicación.  
* **Binarios con Esquema (Avro, Protobuf, Thrift):** Son compactos y eficientes.  
  * *Protobuf/Thrift:* Dependen de etiquetas numéricas de campo. La regla de oro es **nunca cambiar la etiqueta de un campo existente**. Los campos nuevos deben ser siempre opcionales o tener valores por defecto para garantizar la compatibilidad.6  
  * *Avro:* Maneja la evolución de esquema de manera diferente, almacenando el esquema junto con los datos (en archivos) o en un registro de esquemas (en flujos). Es ideal para entornos de Big Data (Hadoop/Data Lakes) donde la estructura de los datos cambia dinámicamente.

## ---

**5\. Replicación: La Distribución de la Verdad**

La replicación consiste en mantener copias de los mismos datos en múltiples nodos conectados por una red. Sus propósitos son triples: **Alta Disponibilidad** (tolerancia a fallos de nodos), **Latencia** (geo-distribución) y **Escalabilidad** (aumentar el throughput de lectura).20

### **5.1. Modelos de Líder y Topologías**

El Agente debe elegir entre tres arquitecturas fundamentales, cada una con un perfil de riesgo/beneficio distinto.

#### **5.1.1. Líder Único (Single-Leader)**

Todas las escrituras se dirigen a un nodo designado (Líder). El líder replica el flujo de cambios a los nodos Seguidores. Las lecturas pueden servirse desde cualquier nodo.

* *Ventaja:* Simplicidad conceptual. Garantiza linealidad en las escrituras (no hay conflictos).  
* *Riesgo:* El líder es un punto único de fallo para las escrituras. Si el líder cae, hay un tiempo de inactividad hasta que se promueve un seguidor (*failover*).

#### **5.1.2. Multi-Líder (Multi-Leader)**

Múltiples nodos aceptan escrituras (comúnmente uno por datacenter en configuraciones geo-distribuidas).

* *Ventaja:* Tolerancia a fallos de red completos (datacenter outage). Mejor latencia de escritura percibida por el usuario local.  
* *Riesgo Crítico:* **Conflictos de Escritura**. Si el Datacenter A cambia la clave $X$ a "valor1" y el Datacenter B cambia $X$ a "valor2" simultáneamente, ¿cuál prevalece? El sistema debe implementar resolución de conflictos (Last-Write-Wins, CRDTs, o lógica personalizada).

#### **5.1.3. Sin Líder (Leaderless / Dynamo-Style)**

Inspirado por el paper de Amazon Dynamo. Cualquier nodo puede aceptar escrituras. No hay líder central.

* Mecanismo de Quórum: Para garantizar la consistencia, las lecturas y escrituras deben solaparse. La fórmula de decisión es:

  $$w \+ r \> n$$

  Donde $w$ es el número de nodos que deben confirmar la escritura, $r$ el número de nodos consultados en lectura, y $n$ el factor de replicación total.  
* *Reparación de Entropía:* Dado que los nodos pueden desincronizarse, se utilizan mecanismos como **Read Repair** (reparar al leer un dato obsoleto) y procesos de fondo de **Anti-Entropy** (usando Árboles de Merkle) para sincronizar réplicas.21

### **5.2. El Problema del Lag de Replicación**

En sistemas asíncronos (la norma para escalabilidad), los seguidores pueden estar retrasados respecto al líder. Esto crea anomalías temporales que el Agente debe saber mitigar 6:

1. **Read-Your-Writes Consistency (Lectura de tus propias escrituras):**  
   * *Escenario:* Un usuario actualiza su perfil y recarga la página inmediatamente. La petición de lectura va a una réplica retrasada que aún tiene el dato viejo. El usuario cree que su cambio se perdió.  
   * *Solución:* Si el usuario ha modificado el dato recientemente (e.g., último minuto), forzar la lectura desde el Líder.  
2. **Monotonic Reads (Lecturas Monotónicas):**  
   * *Escenario:* Un usuario hace varias lecturas sucesivas. La primera va a una réplica actualizada, la segunda a una réplica retrasada. El usuario ve "viajar el tiempo hacia atrás".  
   * *Solución:* Asegurar que un usuario específico siempre lea de la misma réplica (Sticky Routing basado en Hash de UserID).

## ---

**6\. Particionamiento (Sharding): Divide y Vencerás**

Cuando el volumen de datos o la carga de consultas excede la capacidad de una sola máquina, se debe particionar. El objetivo es distribuir la carga uniformemente (Shared Nothing Architecture).

### **6.1. Estrategias de Particionamiento y el Peligro de los Hotspots**

El Agente debe evitar a toda costa los "Hotspots" (nodos desproporcionadamente cargados).

1. **Particionamiento por Rango de Claves (Key Range):** Asignar claves A-C al nodo 1, D-F al nodo 2, etc.  
   * *Ventaja:* Permite consultas de rango eficientes (e.g., escanear todos los usuarios por apellido).  
   * *Riesgo:* Si la clave es un timestamp (muy común), todas las escrituras del día actual irán al mismo nodo, creando un hotspot de escritura masivo mientras los demás nodos están ociosos.6  
2. **Particionamiento por Hash (Hash Partitioning):** Aplicar una función hash a la clave y asignar partición según el hash.  
   * *Ventaja:* Distribuye las claves pseudo-aleatoriamente, eliminando hotspots y equilibrando la carga perfectamente.  
   * *Desventaja:* Destruye el orden de las claves. Las consultas de rango se vuelven ineficientes (Scatter-Gather), ya que deben consultar a todas las particiones.  
   * *Técnica Avanzada:* **Consistent Hashing**. Utilizada para minimizar el movimiento de datos cuando se añaden o eliminan nodos del clúster.22

## ---

**7\. Transacciones: La Ilusión de la Atomicidad**

Las transacciones son una abstracción que permite al programador pretender que ciertos tipos de fallos y problemas de concurrencia no existen. Sin embargo, no todas las transacciones son iguales. El acrónimo ACID es a menudo marketing; lo que importa es el **Nivel de Aislamiento**.27

### **7.1. Niveles de Aislamiento y Anomalías de Concurrencia**

El Agente debe ser capaz de diagnosticar condiciones de carrera sutiles que ocurren bajo carga.

#### **7.1.1. Read Committed (Lectura Confirmada)**

El nivel más básico garantizado por muchas bases de datos (e.g., PostgreSQL default).

* *Garantía:* No leerás datos sucios (sin commit). No sobrescribirás datos sucios.  
* *Vulnerabilidad:* **Lost Updates** (Actualizaciones perdidas). Si dos transacciones leen un contador (valor 10), lo incrementan (+1) y lo escriben, el resultado será 11, no 12\. La segunda escritura "pisa" la primera.  
* *Vulnerabilidad:* **Read Skew** (Lecturas inconsistentes). Si una transacción larga lee la cuenta A, y luego la cuenta B, pero en medio otra transacción transfiere dinero de B a A, la primera transacción verá un estado inconsistente (dinero que desapareció o se duplicó temporalmente).

#### **7.1.2. Snapshot Isolation / Repeatable Read**

Implementado mediante **MVCC (Multi-Version Concurrency Control)**. La base de datos mantiene múltiples versiones de cada objeto.

* *Mecanismo:* Cada transacción lee de una "foto" consistente de la base de datos tomada al inicio de la transacción. Los lectores no bloquean a los escritores y viceversa.  
* *Vulnerabilidad Crítica:* **Write Skew**.  
  * *Escenario Simulado (Doctores de Guardia):* Regla de negocio: "Debe haber al menos un doctor de guardia". Actualmente hay 2 doctores (Alicia y Bob). Ambos se sienten mal y deciden pedir baja simultáneamente.  
    1. Alicia consulta: "¿Cuántos doctores hay?" \-\> 2\.  
    2. Bob consulta: "¿Cuántos doctores hay?" \-\> 2\.  
    3. Alicia actualiza su estado a "Baja" (porque 2-1 \= 1, cumple la regla).  
    4. Bob actualiza su estado a "Baja" (porque 2-1 \= 1, cumple la regla).  
    5. *Resultado:* 0 doctores de guardia.  
  * *Análisis:* Esto no es un conflicto de escritura sucio (modifican filas distintas), ni una actualización perdida. Es una condición de carrera lógica derivada de una premisa que dejó de ser válida. Snapshot Isolation no previene esto.1

#### **7.1.3. Serializable**

El aislamiento más fuerte. Garantiza que el resultado de la ejecución paralela sea equivalente a ejecutarlas una tras otra.

* *Técnicas:*  
  1. **Actual Serial Execution:** (e.g., Redis, VoltDB). Usar un solo hilo de CPU. Extremadamente rápido si todo cabe en memoria y las transacciones son cortas.  
  2. **Two-Phase Locking (2PL):** Bloqueo pesimista. Lento bajo contención.  
  3. **Serializable Snapshot Isolation (SSI):** (e.g., PostgreSQL moderno). Enfoque optimista. Deja ejecutar las transacciones pero rastrea si las premisas de lectura de una transacción fueron modificadas por otra. Si detecta conflicto, aborta una al hacer commit. Es el estado del arte en rendimiento transaccional.31

## ---

**8\. Sistemas Distribuidos: La Realidad Física**

El Agente debe desconfiar de las abstracciones. En un sistema distribuido:

1. **La Red no es fiable:** Los paquetes se pierden, se duplican o se retrasan indefinidamente. No hay forma de distinguir entre un nodo caído y un nodo lento (problema de los Generales Bizantinos / FLP Impossibility).32  
2. **Los Relojes mienten:** El tiempo físico no es confiable. Los relojes de cuarzo derivan (drift). NTP no garantiza sincronización perfecta. El Agente no debe usar System.currentTimeMillis() para ordenar eventos causales. Debe usar **Relojes Lógicos** (Lamport, Vector Clocks) para determinar la causalidad (qué evento causó cuál).21

### **8.1. Consistencia vs. Consenso**

* **Teorema CAP:** En presencia de una Partición de red (P), debes elegir entre Disponibilidad (A) o Consistencia (C).  
  * *Insight:* En sistemas globales, P es un hecho. La elección real es entre rechazar escrituras (CP) o aceptar escrituras divergentes (AP) y reconciliar después.34  
* **Consenso Distribuido (Paxos/Raft):** Es fundamental para coordinadores (como Zookeeper/Etcd) para decidir quién es el líder. Es difícil y costoso.

## ---

**9\. Procesamiento Batch y Stream: Integración de Datos**

Finalmente, la arquitectura moderna se aleja de bases de datos monolíticas hacia flujos de datos.

### **9.1. Stream Processing**

* **Ventanas de Tiempo:** El Agente debe distinguir entre Tumbling (fija), Hopping (deslizante con salto) y Sliding (deslizante continua) para agregaciones.35  
* **Semántica Exactly-Once:** Considerada imposible matemáticamente en redes generales, es lograble en sistemas cerrados (Kafka \+ Flink) mediante **idempotencia** y transacciones distribuidas atómicas.37

## ---

**10\. Conclusión y Ética: La Responsabilidad del Arquitecto**

El diseño de sistemas intensivos en datos es un ejercicio de equilibrio. No existe la herramienta perfecta. Las bases de datos relacionales no son "legado" obsoleto; son herramientas de precisión para garantías fuertes. NoSQL no es "mejor"; es una herramienta de escalabilidad para modelos de datos específicos.

**Heurística Final:** La complejidad es el enemigo. Como cita Kleppmann: "Hacer un sistema más simple no significa reducir su funcionalidad; significa eliminar la **complejidad accidental**".15 Un Agente de IA entrenado bajo estos principios no buscará la solución más novedosa, sino la más aburrida que satisfaga los requisitos de Fiabilidad, Escalabilidad y Mantenibilidad.

---

**Nota sobre Referencias:** Las citas entre corchetes (e.g.1) refieren a los módulos de investigación específicos utilizados para la síntesis de este reporte.

#### **Obras citadas**

1. sonugiri1043/DDIS-Designing-Data-Intensive-App-Notes ... \- GitHub, fecha de acceso: enero 12, 2026, [https://github.com/sonugiri1043/DDIS-Designing-Data-Intensive-App-Notes](https://github.com/sonugiri1043/DDIS-Designing-Data-Intensive-App-Notes)  
2. Designing Data-Intensive Applications (DDIA) — an O'Reilly book by Martin Kleppmann (The Wild Boar Book), fecha de acceso: enero 12, 2026, [https://dataintensive.net/](https://dataintensive.net/)  
3. Twitter's Home Feed Explained Through Designing Data-Intensive Applications (Chapter 1), fecha de acceso: enero 12, 2026, [https://medium.com/@imamarham10/twitters-home-feed-explained-through-designing-data-intensive-applications-chapter-1-478081fd4503](https://medium.com/@imamarham10/twitters-home-feed-explained-through-designing-data-intensive-applications-chapter-1-478081fd4503)  
4. Designing Data-Intensive Applications \- BYUI Store, fecha de acceso: enero 12, 2026, [https://www.byuistore.com/Designing-Data-Intensive-Applications](https://www.byuistore.com/Designing-Data-Intensive-Applications)  
5. Designing Data Intensive Applications \- www.ec-undp-electoralassistance.org, fecha de acceso: enero 12, 2026, [https://www.ec-undp-electoralassistance.org/index.jsp/textbook-solutions/xlZ2pR/Designing%20Data%20Intensive%20Applications.pdf](https://www.ec-undp-electoralassistance.org/index.jsp/textbook-solutions/xlZ2pR/Designing%20Data%20Intensive%20Applications.pdf)  
6. learning-notes/books/designing-data-intensive-applications.md at ..., fecha de acceso: enero 12, 2026, [https://github.com/keyvanakbary/learning-notes/blob/master/books/designing-data-intensive-applications.md](https://github.com/keyvanakbary/learning-notes/blob/master/books/designing-data-intensive-applications.md)  
7. fecha de acceso: enero 12, 2026, [https://timilearning.com/posts/ddia/part-one/chapter-1/\#:\~:text=Reliability%20means%20making%20systems%20work,to%20work%20with%20the%20system.](https://timilearning.com/posts/ddia/part-one/chapter-1/#:~:text=Reliability%20means%20making%20systems%20work,to%20work%20with%20the%20system.)  
8. Chapter 1 \- Reliable, Scalable and Maintainable Applications, fecha de acceso: enero 12, 2026, [https://timilearning.com/posts/ddia/part-one/chapter-1/](https://timilearning.com/posts/ddia/part-one/chapter-1/)  
9. Reliability, Scalability and Maintainability | Otee's Notes on Programming, fecha de acceso: enero 12, 2026, [https://otee.dev/2021/12/10/ddia-notes-chapter-1.html](https://otee.dev/2021/12/10/ddia-notes-chapter-1.html)  
10. ahmedhammad97/Designing-Data-Intensive-Applications-Notes \- GitHub, fecha de acceso: enero 12, 2026, [https://github.com/ahmedhammad97/Designing-Data-Intensive-Applications-Notes](https://github.com/ahmedhammad97/Designing-Data-Intensive-Applications-Notes)  
11. Scalability, Reliability & Maintainability — Core Concepts of System Design \- Medium, fecha de acceso: enero 12, 2026, [https://medium.com/@190160116149.parth/scalability-reliability-maintainability-core-concepts-of-system-design-7efb020783c1](https://medium.com/@190160116149.parth/scalability-reliability-maintainability-core-concepts-of-system-design-7efb020783c1)  
12. Scalability : Twitter's Journey. Reference \- Designing Data Intensive… | by Siddhant Sambit, fecha de acceso: enero 12, 2026, [https://medium.com/@siddhantsambit/scalability-twitters-journey-16ed5af2e01b](https://medium.com/@siddhantsambit/scalability-twitters-journey-16ed5af2e01b)  
13. How Twitter handled personalized timelines for their users | Arkadiusz Chmura, fecha de acceso: enero 12, 2026, [https://arkadiuszchmura.com/posts/how-twitter-handled-personalized-timelines-for-their-users/](https://arkadiuszchmura.com/posts/how-twitter-handled-personalized-timelines-for-their-users/)  
14. book-notes/designing-data-intensive-applications.markdown at ..., fecha de acceso: enero 12, 2026, [https://github.com/mgp/book-notes/blob/master/designing-data-intensive-applications.markdown](https://github.com/mgp/book-notes/blob/master/designing-data-intensive-applications.markdown)  
15. Designing Data-Intensive Applications Book Notes, Quotes and Highlights | Screvi, fecha de acceso: enero 12, 2026, [https://screvi.com/highlights/designing-data-intensive-applications/](https://screvi.com/highlights/designing-data-intensive-applications/)  
16. Designing data-intensive applications: the big ideas behind reliable, scalable, and maintainable systems \[1 ed.\] 9781449373320, 1449373321 \- DOKUMEN.PUB, fecha de acceso: enero 12, 2026, [https://dokumen.pub/designing-data-intensive-applications-the-big-ideas-behind-reliable-scalable-and-maintainable-systems-1nbsped-9781449373320-1449373321.html](https://dokumen.pub/designing-data-intensive-applications-the-big-ideas-behind-reliable-scalable-and-maintainable-systems-1nbsped-9781449373320-1449373321.html)  
17. Write throughput differences in B-tree vs LSM-tree based databases? \- Reddit, fecha de acceso: enero 12, 2026, [https://www.reddit.com/r/databasedevelopment/comments/187cp1g/write\_throughput\_differences\_in\_btree\_vs\_lsmtree/](https://www.reddit.com/r/databasedevelopment/comments/187cp1g/write_throughput_differences_in_btree_vs_lsmtree/)  
18. Revisiting B+-tree vs. LSM-tree \- USENIX, fecha de acceso: enero 12, 2026, [https://www.usenix.org/publications/loginonline/revisit-b-tree-vs-lsm-tree-upon-arrival-modern-storage-hardware-built](https://www.usenix.org/publications/loginonline/revisit-b-tree-vs-lsm-tree-upon-arrival-modern-storage-hardware-built)  
19. B-Tree vs LSM-Tree \- TiKV, fecha de acceso: enero 12, 2026, [https://tikv.org/deep-dive/key-value-engine/b-tree-vs-lsm/](https://tikv.org/deep-dive/key-value-engine/b-tree-vs-lsm/)  
20. Data-Engineering-Books/Book-2Designing-data-intensive-applications.pdf at main \- GitHub, fecha de acceso: enero 12, 2026, [https://github.com/letthedataconfess/Data-Engineering-Books/blob/main/Book-2Designing-data-intensive-applications.pdf](https://github.com/letthedataconfess/Data-Engineering-Books/blob/main/Book-2Designing-data-intensive-applications.pdf)  
21. Dynamo: Amazon's Highly Available Key-value Store \- All Things Distributed, fecha de acceso: enero 12, 2026, [https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf)  
22. CS 739 Reviews \- Fall 2014: \- cs.wisc.edu, fecha de acceso: enero 12, 2026, [https://pages.cs.wisc.edu/\~swift/classes/cs739-fa14/blog/2014/09/post.html](https://pages.cs.wisc.edu/~swift/classes/cs739-fa14/blog/2014/09/post.html)  
23. Book notes: Designing Data-Intensive Applications \- Daniel Lebrero, fecha de acceso: enero 12, 2026, [https://danlebrero.com/2021/09/01/designing-data-intensive-applications-summary/](https://danlebrero.com/2021/09/01/designing-data-intensive-applications-summary/)  
24. Reading Your Own Writes \- Designing Data-Intensive Applications. The Big Ideas Behind Reliable, Scalable and Maintainable Syst, fecha de acceso: enero 12, 2026, [https://ebrary.net/64708/computer\_science/reading\_your\_writes](https://ebrary.net/64708/computer_science/reading_your_writes)  
25. Data Partitioning Cheat Sheet (Practical Guide for Developers) | by Jaya Sandeep Ketha, fecha de acceso: enero 12, 2026, [https://medium.com/@kethajayasandeep1254/data-partitioning-cheat-sheet-641dc639f7ef](https://medium.com/@kethajayasandeep1254/data-partitioning-cheat-sheet-641dc639f7ef)  
26. Partitioning in Distributed Data Systems: Explained with Real-World Examples, fecha de acceso: enero 12, 2026, [https://dev.to/dhanush\_\_\_b/partitioning-in-distributed-data-systems-explained-with-real-world-examples-356e](https://dev.to/dhanush___b/partitioning-in-distributed-data-systems-explained-with-real-world-examples-356e)  
27. Designing Data Intensive Applications: Transactions with Weak Isolation | by Adrian Booth, fecha de acceso: enero 12, 2026, [https://medium.com/@adrianbooth/designing-data-intensive-applications-transactions-with-weak-isolation-3ba6a80a67e8](https://medium.com/@adrianbooth/designing-data-intensive-applications-transactions-with-weak-isolation-3ba6a80a67e8)  
28. Chapter 7 \- Transactions, fecha de acceso: enero 12, 2026, [https://timilearning.com/posts/ddia/part-two/chapter-7/](https://timilearning.com/posts/ddia/part-two/chapter-7/)  
29. 'Lost update' vs 'Write skew' \- sql \- Stack Overflow, fecha de acceso: enero 12, 2026, [https://stackoverflow.com/questions/27826714/lost-update-vs-write-skew](https://stackoverflow.com/questions/27826714/lost-update-vs-write-skew)  
30. DDIA: Chp 7\. Transactions (Part 1\) \- Murat Buffalo, fecha de acceso: enero 12, 2026, [http://muratbuffalo.blogspot.com/2024/10/ddia-chp-7-transactions-part-1.html](http://muratbuffalo.blogspot.com/2024/10/ddia-chp-7-transactions-part-1.html)  
31. DDIA: Chp 7\. Transactions (Part 2): Serializability \- Metadata, fecha de acceso: enero 12, 2026, [http://muratbuffalo.blogspot.com/2024/10/ddia-chp-7-transactions-part-2.html](http://muratbuffalo.blogspot.com/2024/10/ddia-chp-7-transactions-part-2.html)  
32. DynamoDB: Amazon's Highly Available, Eventually Consistent Key-Value Store Explained, fecha de acceso: enero 12, 2026, [https://dev.to/dhanush\_\_\_b/dynamodb-amazons-highly-available-eventually-consistent-key-value-store-explained-4l72](https://dev.to/dhanush___b/dynamodb-amazons-highly-available-eventually-consistent-key-value-store-explained-4l72)  
33. Designing Data-Intensive Applications \- Timothy Andrew, fecha de acceso: enero 12, 2026, [https://timothya.com/learning/designing-data-intensive-applications/](https://timothya.com/learning/designing-data-intensive-applications/)  
34. Please stop calling databases CP or AP \- Martin Kleppmann, fecha de acceso: enero 12, 2026, [https://martin.kleppmann.com/2015/05/11/please-stop-calling-databases-cp-or-ap.html](https://martin.kleppmann.com/2015/05/11/please-stop-calling-databases-cp-or-ap.html)  
35. Introduction to Azure Stream Analytics windowing functions \- Microsoft Learn, fecha de acceso: enero 12, 2026, [https://learn.microsoft.com/en-us/azure/stream-analytics/stream-analytics-window-functions](https://learn.microsoft.com/en-us/azure/stream-analytics/stream-analytics-window-functions)  
36. knowledge-sharing/51. DDIA-Stream Processing.md at master \- GitHub, fecha de acceso: enero 12, 2026, [https://github.com/xinrong-meng/knowledge-sharing/blob/master/51.%20DDIA-Stream%20Processing.md](https://github.com/xinrong-meng/knowledge-sharing/blob/master/51.%20DDIA-Stream%20Processing.md)  
37. Exactly-once Support in Apache Kafka | by Jay Kreps \- Medium, fecha de acceso: enero 12, 2026, [https://medium.com/@jaykreps/exactly-once-support-in-apache-kafka-55e1fdd0a35f](https://medium.com/@jaykreps/exactly-once-support-in-apache-kafka-55e1fdd0a35f)  
38. Exactly-once Semantics is Possible: Here's How Apache Kafka Does it \- Confluent, fecha de acceso: enero 12, 2026, [https://www.confluent.io/blog/exactly-once-semantics-are-possible-heres-how-apache-kafka-does-it/](https://www.confluent.io/blog/exactly-once-semantics-are-possible-heres-how-apache-kafka-does-it/)