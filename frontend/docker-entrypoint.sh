#!/bin/sh
# Custom entrypoint that logs every step so we can debug Railway deploy failures.
set -e

echo "=== ENTRYPOINT START ==="
echo "PORT=${PORT:-NOT_SET}"
echo "VITE_API_URL=${VITE_API_URL:-NOT_SET}"
echo "HOME=$HOME"
echo "PWD=$(pwd)"

echo "=== Processing nginx template ==="
envsubst '${PORT} ${VITE_API_URL} ${BACKEND_PRIVATE_URL}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

echo "=== Generated nginx config ==="
cat /etc/nginx/conf.d/default.conf

echo "=== Testing nginx config ==="
nginx -t

echo "=== Starting nginx ==="
exec nginx -g 'daemon off;'
