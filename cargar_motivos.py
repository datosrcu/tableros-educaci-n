from alumnos.models import MotivoJustificacion

nuevos_motivos = [
    "Problemas de salud",
    "Cita médica / Odontológica",
    "Trámites familiares",
    "Problemas de transporte",
    "Viaje familiar",
    "Emergencia familiar",
    "Clima adverso"
]

for motivo in nuevos_motivos:
    MotivoJustificacion.objects.get_or_create(nombre=motivo)

print("Motivos de justificación actualizados.")
