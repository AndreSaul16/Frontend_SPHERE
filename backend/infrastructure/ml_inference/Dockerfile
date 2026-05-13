# Usamos una imagen base temporalmente (en producción usarás una con CUDA)
FROM python:3.11-slim

# Configuramos el directorio de trabajo
WORKDIR /app

# Instalamos dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copiamos las dependencias primero para aprovechar la caché de Docker
COPY requirements.txt .

# Instalamos dependencias de Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código
COPY . .

# Exponemos el puerto que usará el servicio
EXPOSE 8000

# Comando por defecto (placeholder)
# En producción, esto ejecutará el servidor de inferencia
# Placeholder hasta la Fase 3
CMD ["sleep", "infinity"]
