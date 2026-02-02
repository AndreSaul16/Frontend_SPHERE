# Usamos una imagen ligera de Node.js
FROM node:20-alpine

# Directorio de trabajo
WORKDIR /app

# Copiamos los archivos de dependencias primero para aprovechar el caché
COPY package*.json ./

# Instalamos dependencias
RUN npm install

# Copiamos el resto del código
COPY . .

# Exponemos el puerto de Vite
EXPOSE 3000

# Comando por defecto para desarrollo
# --host 0.0.0.0 es necesario para que sea accesible desde fuera del contenedor
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
