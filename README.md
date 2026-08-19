# Tableros de Gestión Educativa - Secretaría de Educación

Este repositorio contiene los **5 Tableros de Gestión por Programa** desarrollados para el monitoreo, analítica y gestión operativa en tiempo real de los programas educativos municipales.

---

## 📊 Tableros Incluidos

1. **Primera Infancia - Espacios Lúdicos y de Aprendizaje** (`/espacios-ludicos/`)
   - Monitoreo integral de Jardines Maternales municipales y Salas Cuna.
2. **Programa Municipal de Alfabetización y Acompañamiento Educativo** (`/alfabetizacion/`)
   - Gestión de centros de alfabetización, apoyo escolar e inclusión educativa.
3. **Escuela Municipal de Carpintería** (`/carpinteria/`)
   - Analítica de matriculados, capacitaciones en oficios y asistencia técnica.
4. **Escuela Municipal de Artes Plásticas Manuel Belgrano** (`/artes-plasticas/`)
   - Seguimiento de talleres artísticos, cupos y asistencias.
5. **Programa Expresión Cultural** (`/expresion-cultural/`)
   - Monitoreo de actividades culturales territoriales y centros comunitarios.

---

## 🚀 Características

- **Diseño Responsivo e Institucional**: Header oficial `#009de0`, logos institucionales Base64, modales explicativos de IA y glosario interactivo.
- **Geolocalización Territorial**: Mapas con Leaflet.js integrando ubicaciones exactas por sector y zona.
- **Analítica de Costos en Tiempo Real**: Cálculo de costo por alumno y costo total docente integrado mediante Google Sheets API / Cache local.
- **Matriz de Asistencia Mensual**: Tabla interactiva desglosada por espacio, turno, sala y días del mes.
- **Gráficos Dinámicos**: Tendencias de inscripciones de últimos 6 meses (Chart.js) y distribución por zonas.

---

## 🔧 Instalación y Ejecución Local

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/datosrcu/tableros-educaci-n.git
   cd tableros-educaci-n
   ```

2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Aplicar migraciones e iniciar servidor:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

4. Abrir en el navegador: `http://127.0.0.1:8000/`
