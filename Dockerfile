FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

# 🛡️ Usuario no-root para seguridad
RUN useradd -m django-user

COPY . .
RUN chmod +x docker-entrypoint.sh

# Crear directorios para estáticos y media con permisos correctos
RUN mkdir -p /app/staticfiles /app/media && \
    chown -R django-user:django-user /app

RUN python manage.py collectstatic --noinput || true

USER django-user

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]