# Usar imagen oficial de Python slim para reducir tamaño
FROM python:3.12-slim

# Evitar que Python genere archivos .pyc y habilitar modo sin buffer para logs
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Directorio de trabajo en el contenedor
WORKDIR /app

# Instalar dependencias del sistema necesarias para mysqlclient y utilidades básicas
RUN apt-get update && apt-get install -y \
    pkg-config \
    default-libmysqlclient-dev \
    build-essential \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias de Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código del proyecto
COPY . /app/

# Dar permisos de ejecución al entrypoint
RUN chmod +x /app/docker-entrypoint.sh

# Exponer el puerto predeterminado de Django
EXPOSE 8000

# Usar el script de entrada para migraciones y arranque
ENTRYPOINT ["/app/docker-entrypoint.sh"]
