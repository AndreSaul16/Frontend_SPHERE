# Usamos una imagen ligera de Node, ya que usaremos React (Node.js)
FROM node:20-alpine

# Establecemos el directorio de trabajo
WORKDIR /app

# Copiamos el archivo de dependencias (necesario para el build)
COPY package.json .

# Instalamos dependencias (aunque sea un placeholder)
RUN npm install

# Creamos un archivo principal vacío para satisfacer el COPY.
RUN echo "{}" > index.html

# Exponemos el puerto que usará React en desarrollo
EXPOSE 3000

# Comando de inicio: por ahora, solo mantiene vivo el contenedor
CMD ["sleep", "infinity"]
