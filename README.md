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

## 🛠️ Tecnologías y Arquitectura

- **Backend**: Django 5.2 (Python 3.12+)
- **Base de Datos**: Configuración agnóstica mediante `dj-database-url`. Soporte nativo para PostgreSQL, MySQL y SQLite.
- **Seguridad**: Gestión de variables de entorno con `python-decouple`.
- **Frontend**: Diseño responsive basado en Bootstrap 5 con estética premium y micro-animaciones.
- **Servidor de Producción**: Preparado para WhiteNoise (estáticos) y Gunicorn/Daphne.

---

## 🚀 Guía de Instalación Profesional

### 1. Requisitos
- Python 3.12+
- PostgreSQL / MySQL (Opcionales, SQLite por defecto)

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

### 3. Variables de Entorno
El sistema utiliza un archivo `.env` para la configuración sensible. Existe una plantilla disponible:
```bash
cp .env.example .env
```
> [!IMPORTANT]
> Asegúrate de generar una `SECRET_KEY` única y configurar la `DATABASE_URL` según tu entorno.

### 4. Preparación de Base de Datos
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Utilidades de Configuración Inicial
Existen scripts para facilitar el primer despliegue:
```bash
# Crear cuentas base (admin, coordinador_test, docente_test)
python manage.py shell < crear_cuentas_base.py

# (Opcional) Cargar motivos de justificación estandarizados
python manage.py shell < cargar_motivos.py
```

---

## 🏗️ Despliegue en Producción

Para entornos de producción, se recomienda utilizar un servidor WSGI como **Gunicorn**:

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

El proyecto ya incluye la configuración de **WhiteNoise** para servir archivos estáticos de forma eficiente sin necesidad de un servidor separado para los mismos.

---

## 👥 Contribuidores
- **Marcos Saez** - [GitHub](https://github.com/marcos-225)
- **Gobierno de Río Cuarto** - [Región Digital](https://github.com/gobderiocuarto)

---
© 2026 Sistema Jardines - Gestión Educativa Municipal
