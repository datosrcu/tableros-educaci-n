from django.db import migrations

def crear_tipos_default(apps, schema_editor):
    TipoActividadEspecial = apps.get_model('jardines', 'TipoActividadEspecial')
    tipos_default = [
        ("Festejos / Eventos Institucionales", "Actividades institucionales, celebraciones y eventos comunitarios o festivos."),
        ("Capacitaciones", "Talleres, capacitaciones obligatorias, cursos formativos y actualización pedagógica."),
        ("Jornadas Pedagógicas", "Reuniones de equipo docente, planificación pedagógica y jornadas institucionales."),
        ("Comisiones de Servicio", "Trámites, representaciones institucionales y tareas fuera del establecimiento habitual."),
    ]
    for nombre, descripcion in tipos_default:
        TipoActividadEspecial.objects.get_or_create(
            nombre=nombre,
            defaults={
                "descripcion": descripcion,
                "es_default": True,
                "activo": True
            }
        )

def revertir_tipos_default(apps, schema_editor):
    TipoActividadEspecial = apps.get_model('jardines', 'TipoActividadEspecial')
    TipoActividadEspecial.objects.filter(es_default=True).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('jardines', '0021_tipoactividadespecial_alter_asistenciadocente_estado_and_more'),
    ]

    operations = [
        migrations.RunPython(crear_tipos_default, revertir_tipos_default),
    ]
