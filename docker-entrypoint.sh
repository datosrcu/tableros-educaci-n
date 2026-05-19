#!/bin/bash

# docker-entrypoint.sh
# Script para esperar a la base de datos y ejecutar migraciones antes de iniciar el servidor.

set -e

echo "Esperando a que la base de datos en $DB_HOST:$DB_PORT esté lista..."

RETRIES=30
while ! python -c "import socket; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(1); s.connect(('$DB_HOST', int('$DB_PORT' or 3306))); s.close()" 2>/dev/null; do
  RETRIES=$((RETRIES-1))
  if [ $RETRIES -le 0 ]; then
    echo "No se pudo conectar a la base de datos tras múltiples intentos. Abortando."
    exit 1
  fi
  echo "La base de datos no responde... reintentando en 2 segundos. ($RETRIES intentos restantes)"
  sleep 2
done

echo "Base de datos disponible."

# Ejecutar migraciones
echo "Ejecutando migraciones de Django..."
python manage.py migrate --noinput

# Recolectar archivos estáticos
echo "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

# Iniciar la aplicación (el comando viene de docker-compose.yml)
exec "$@"
