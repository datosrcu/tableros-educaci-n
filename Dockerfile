FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

# Dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    default-mysql-client \
    pkg-config \
    curl \
    netcat-openbsd \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Usuario no root
RUN useradd -m django-user

COPY . .

RUN chmod +x docker-entrypoint.sh

# Directorios necesarios
RUN mkdir -p /app/staticfiles /app/media && \
    chown -R django-user:django-user /app

USER django-user

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]