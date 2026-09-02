# Sistema de Control de Asistencia y Gestión Educativa 🌱

[![Django](https://img.shields.io/badge/Django-5.2-092e20?style=for-the-badge&logo=django)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.12+-3776ab?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-563d7c?style=for-the-badge&logo=bootstrap)](https://getbootstrap.com/)

Sistema integral para la gestión de jardines de infantes, diseñado para simplificar el control de asistencia, la gestión de alumnos y la administración institucional a través de tableros específicos por roles.

---

## ✨ Características Principales

### 👨‍🏫 Panel Docente (Premium)
- **Dashboard de Trabajo**: Gestión centralizada de salas asignadas.
- **Control de Asistencia Avanzado**:
    - Estados: Presente, Ausente, **Llegada Tarde** y **Retiro Temprano**.
    - Motivos de justificación integrados y dinámicos.
- **Gestión de Alumnos**: Registro y edición con legajos completos.
- **Historial Detallado**: Visualización gráfica y exportable de asistencias.

### 🏢 Módulo de Coordinación y Auditoría
- **Supervisión Jerárquica**: Administración de Programas, Subprogramas, Jardines y Salas.
- **Asignación de Personal**: Vinculación flexible de docentes a múltiples salas.
- **Seguridad y Usuarios**:
    - **Restablecimiento de Contraseñas**: Función para que coordinadores asistan a docentes.
    - **Seguridad por Roles**: Acceso restringido y validado.
- **Log de Auditoría**: Registro completo de creación, edición y eliminación de datos sensibles.

### 📊 Reportes y Exportación
- **Exportación masiva**: Generación de reportes en formato CSV.
- **Vistas de Impresión**: Diseño optimizado para imprimir listados de alumnos y asistencias.

---

## 🏗️ Despliegue con Docker (Recomendado)

El sistema está completamente contenedorizado para facilitar su despliegue en cualquier entorno.

### 1. Iniciar el Sistema
Asegúrate de tener Docker instalado y luego ejecuta:
```bash
docker compose up -d --build
```

### 2. Inicialización de Datos
Para crear las cuentas base y cargar los datos iniciales dentro del contenedor:
```bash
docker exec jardines_web python crear_cuentas_base.py
```

### 3. Acceso
La aplicación estará disponible en `http://localhost:8000`.

### 🛠️ Comandos de Mantenimiento
- **Detener el sistema**: `docker compose stop` (los contenedores se pausan pero no se eliminan).
- **Reiniciar el sistema**: `docker compose start`.
- **Apagar y limpiar**: `docker compose down` (detiene y elimina los contenedores y redes virtuales).
- **Ver logs en tiempo real**: `docker compose logs -f`.

---

## 🔧 Modo Mantenimiento

El sistema cuenta con una pantalla institucional de mantenimiento que se activa mediante una variable de entorno en Dokploy o en el `.env`, sin necesidad de tocar código ni la base de datos.
Cuando está activo, **todos los accesos al sistema** (salvo `/health/` y estáticos) son interceptados y responden con la pantalla de aviso oficial.

### ▶️ Activar el mantenimiento

**Opción A – vía panel de Dokploy (Producción):**
1. Ingresar al panel de Dokploy → Aplicación → **Environment Variables**
2. Agregar o editar:
   ```env
   MAINTENANCE_MODE=true
   ```
   *(También acepta `1`, `True`, `yes`, con o sin comillas)*
3. Hacer **Redeploy** (o Save & Restart).

**Opción B – vía `.env` local:**
```env
MAINTENANCE_MODE=true
```

**Opción C – mediante archivo flag en el contenedor:**
Crear un archivo vacío `maintenance.flag` en la raíz del proyecto o en `/tmp/maintenance.flag`.

---

### ⏹️ Desactivar el mantenimiento (Volver a la normalidad)

**Opción A – vía panel de Dokploy (Producción):**
1. En Dokploy → **Environment Variables**, cambiar a:
   ```env
   MAINTENANCE_MODE=false
   ```
   *(o `0`, `False`, `off`)*
2. Hacer **Redeploy**.

**Opción B – vía `.env` local:**
```env
MAINTENANCE_MODE=false
```

> **🛡️ Nota de Resiliencia:** El parser de variables de entorno limpia automáticamente comillas (`"true"`, `'false'`), espacios accidentales y mayúsculas/minúsculas para evitar cualquier falla de despliegue en Dokploy.

### 🛡️ Rutas que nunca son bloqueadas

| Ruta | Propósito |
|---|---|
| `/health/`, `/healthz`, `/ping` | Healthcheck de Docker y Dokploy |
| `/static/` | Archivos estáticos (CSS, JS, imágenes) |
| `/media/` | Archivos de medios subidos |
| `/favicon.ico` | Ícono del sitio |
| `?bypass_mantenimiento=grcu_admin_2026` | Bypass administrativo para pruebas |

---

## 🛠️ Instalación Local (Desarrollo)

Si prefieres ejecutar el sistema sin Docker, sigue estos pasos:

### 1. Requisitos
- Python 3.12+
- MySQL 8.0 o SQLite

### 2. Configuración del Entorno
```bash
# Clonar y entrar
git clone https://github.com/gobderiocuarto/control_asistencia_educacion.git
cd sistema-jardines

# Crear y activar entorno virtual
python3 -m venv env
source env/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Variables de Envorno
Copia la plantilla y configura tu `DATABASE_URL`:
```bash
cp .env.example .env
```
Para SQLite (local): `DATABASE_URL=sqlite:///db.sqlite3`
Para MySQL (local): `DATABASE_URL=mysql://user:pass@localhost:3306/db_name`

### 4. Preparación y Cuentas Base
```bash
python manage.py migrate
python crear_cuentas_base.py
```

---

## 🚀 Despliegue en Producción

Para entornos de producción sin Docker, se recomienda utilizar un servidor WSGI como **Gunicorn**:

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

El proyecto utiliza **WhiteNoise** para servir archivos estáticos y está configurado para conectarse a bases de datos de producción mediante la variable de entorno `DATABASE_URL`.

---

## 👥 Contribuidores
- **Marcos Saez** - [GitHub](https://github.com/marcos-225)
- **Gobierno de Río Cuarto** - [Región Digital](https://github.com/gobderiocuarto)

---
© 2026 Sistema Jardines - Gestión Educativa Municipal
