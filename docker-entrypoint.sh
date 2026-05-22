#!/bin/bash

# docker-entrypoint.sh
# Script para esperar a la base de datos y ejecutar migraciones antes de iniciar el servidor.

set -e

echo "Esperando a que la base de datos en $DB_HOST:$DB_PORT esté lista..."

RETRIES=30
until python -c "
import django, os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from django.db import connections
try:
    connections['default'].ensure_connection()
    print('OK')
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null; do
  RETRIES=$((RETRIES-1))
  if [ $RETRIES -le 0 ]; then
    echo "No se pudo conectar a la base de datos tras múltiples intentos. Abortando."
    exit 1
  fi
  echo "La base de datos no responde... reintentando en 5 segundos. ($RETRIES intentos restantes)"
  sleep 5
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
