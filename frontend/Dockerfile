# ---- Stage 1: Build ----
FROM node:20-alpine AS build

WORKDIR /app

# Install dependencies (cached layer)
COPY package*.json ./
RUN npm ci

# Copy source and build
COPY . .

# Build with placeholder; nginx substitutes real URL at container start.
# VITE_FIREBASE_* must be present at BUILD time (Vite embeds them into the bundle).
# Railway service variables are runtime-only; we pass Firebase config explicitly here.
RUN VITE_API_URL=__VITE_API_URL__ \
    VITE_FIREBASE_API_KEY=AIzaSyBogAXbPBKAtdogyXPiBinv6e_d2PWX_Sg \
    VITE_FIREBASE_AUTH_DOMAIN=sphere-2a4cf.firebaseapp.com \
    VITE_FIREBASE_PROJECT_ID=sphere-2a4cf \
    VITE_FIREBASE_STORAGE_BUCKET=sphere-2a4cf.firebasestorage.app \
    VITE_FIREBASE_MESSAGING_SENDER_ID=1018425350443 \
    VITE_FIREBASE_APP_ID=1:1018425350443:web:9e32ead8592800594d8d6e \
    npm run build

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

# Custom entrypoint with debug logging for Railway troubleshooting
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Railway handles healthcheck via healthcheckPath in railway.toml.
# No Docker HEALTHCHECK — it races with nginx startup and conflicts with Railway's own probe.
ENV PORT=3000

EXPOSE 3000

ENTRYPOINT ["/docker-entrypoint.sh"]
