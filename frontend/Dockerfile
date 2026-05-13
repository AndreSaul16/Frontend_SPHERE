# ---- Stage 1: Build ----
FROM node:20-alpine AS build

WORKDIR /app

# Install dependencies (cached layer)
COPY package*.json ./
RUN npm ci

# Copy source and build
COPY . .

# VITE_API_URL: bake into build (fallback for local dev)
ARG VITE_API_URL=http://localhost:8000/api/v1
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# ---- Stage 2: Production (nginx) ----
FROM nginx:alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# nginx:alpine procesa automáticamente /etc/nginx/templates/*.template con envsubst
# expandiendo variables de entorno (entre ellas $PORT inyectada por Railway).
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Permisos para que el entrypoint default pueda escribir confs procesados.
RUN chown -R nginx:nginx /usr/share/nginx/html

# Default si Railway no inyecta PORT (dev local).
ENV PORT=3000

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
