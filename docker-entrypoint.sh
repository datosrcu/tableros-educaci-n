#!/bin/bash

# docker-entrypoint.sh
# Script para esperar a la base de datos y ejecutar migraciones antes de iniciar el servidor.

set -e

echo "Esperando a que la base de datos en $DB_HOST:$DB_PORT esté lista..."

while ! nc -z $DB_HOST $DB_PORT; do
  sleep 1
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
