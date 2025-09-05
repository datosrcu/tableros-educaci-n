# Sistema de Gestión de Jardines 🌱

Proyecto en **Django** para la gestión de jardines de infantes, incluyendo:
- Gestión de salas y docentes
- Control de asistencias
- Panel de administración

## 🚀 Requisitos
- Python 3.12+
- PostgreSQL
- Virtualenv (`python3 -m venv`)

## ⚙️ Instalación
1. Clonar el repositorio:
   ```bash
   git clone https://github.com/tuusuario/sistema-jardines.git
   cd sistema-jardines
2. Crear entorno virtual e instalar dependencias:
    ```bash
    python3 -m venv env
    source env/bin/activate
    pip install -r requirements.txt
3. Configurar variables de entorno en .env (ejemplo en .env.example):
    ```bash
    DEBUG=True
    SECRET_KEY=clave_secreta
    DB_NAME=sistema_jardines
    DB_USER=usuario
    DB_PASSWORD=contraseña
    DB_HOST=localhost
    DB_PORT=5432
4. Aplicar migraciones y crear superusuario:
    ```bash
    python manage.py migrate
    python manage.py createsuperuser
5. Ejecuta el servidor:
  ```bash 
    python manage.py runserver
   
## 👥 Usuarios

- Administradores: acceso completo desde el panel /admin/.

- Docentes: acceso al dashboard con control de asistencia.

