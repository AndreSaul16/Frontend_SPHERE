# ---- Stage 1: Build ----
FROM node:20-alpine AS build

WORKDIR /app

# Install dependencies (cached layer)
COPY package*.json ./
RUN npm ci

# Copy source and build
COPY . .

# Build with placeholder; nginx substitutes real URL at container start
RUN VITE_API_URL=__VITE_API_URL__ npm run build

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

# Install curl for HEALTHCHECK (nginx:alpine base lacks it)
RUN apk add --no-cache curl

# Default si Railway no inyecta PORT (dev local).
ENV PORT=3000

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD curl -f http://localhost:${PORT:-3000}/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
