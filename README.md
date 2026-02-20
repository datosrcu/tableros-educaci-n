# Sistema de Control de Asistencia y Gestión Educativa 🌱

[![Django](https://img.shields.io/badge/Django-5.2-092e20?style=for-the-badge&logo=django)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.12+-3776ab?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

Sistema integral para la gestión de jardines de infantes, diseñado para simplificar el control de asistencia, la gestión de alumnos y la administración institucional a través de tableros específicos por roles.

---

## ✨ Características Principales

### 👨‍🏫 Módulo de Docentes
- **Dashboard Personalizado**: Vista rápida de la sala asignada.
- **Control de Asistencia**: Carga dinámica y rápida de asistencias diarias.
- **Gestión de Alumnos**: Registro y edición de estudiantes con formularios dinámicos.
- **Historial de Asistencias**: Visualización detallada por sala.

### 🏢 Módulo de Coordinación
- **Dashboard Estratégico**: Resumen de programas y subprogramas.
- **Gestión Jerárquica**: Administración de Programas, Subprogramas y Salas.
- **Asignación de Personal**: Vinculación de docentes a salas específicas.
- **Monitoreo**: Supervisión general del estado de los jardines.

### 📝 Formularios Dinámicos
- Estructuras de datos flexibles para capturar información específica de alumnos sin cambios de código.

---

## 🛠️ Tecnologías

- **Backend**: Django 5.2 (Python 3.12+)
- **Base de Datos**: Soporte para PostgreSQL y MySQL (configuración vía `.env`).
- **Frontend**: Templates de Django con diseño premium y adaptable.
- **Configuración**: `python-decouple` para gestión de variables de entorno.

---

## 🚀 Instalación y Configuración

### 1. Requisitos Previos
Asegúrate de tener instalado Python 3.12 o superior y un gestor de base de datos.

### 2. Clonar el Proyecto
```bash
git clone https://github.com/gobderiocuarto/control_asistencia_educacion.git
cd sistema-jardines
```

### 3. Entorno Virtual
```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Variables de Envorno
Copia el archivo de ejemplo y configura tus credenciales:
```bash
cp .env.example .env
```
Edita `.env` con tus datos de base de datos y clave secreta.

### 5. Base de Datos y Superusuario
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 6. Ejecución
```bash
python manage.py runserver
```

---

## 🏗️ Arquitectura del Proyecto

- `config/`: Configuración central del proyecto Django.
- `users/`: Gestión de usuarios, roles y middleware de acceso.
- `jardines/`: Lógica central de programas, subprogramas y salas.
- `alumnos/`: Gestión de estudiantes y legajos.
- `formularios/`: Módulo de formularios dinámicos y respuestas.
- `templates/`: Plantillas HTML organizadas por módulo.

---

## 👥 Contribuidores
- **Marcos Saez** - [GitHub]()
- **Gobierno de Río Cuarto** - [GitHub](https://github.com/gobderiocuarto)

---
© 2026 Sistema Jardines - Río Cuarto
