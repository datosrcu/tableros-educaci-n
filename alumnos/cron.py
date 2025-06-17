from django_cron import CronJobBase, Schedule
from django.core.mail import send_mail
from io import StringIO
from django.core.management import call_command

class InformeMantenimientoCron(CronJobBase):
    RUN_AT_TIMES = ['07:00']  # hora servidor (puede ajustarse)

    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'alumnos.informe_mantenimiento_cron'

    def do(self):
        buffer = StringIO()
        buffer.write("🧠 Informe semanal de mantenimiento del sistema:\n\n")

        buffer.write("🔎 Verificando alumnos inválidos:\n")
        call_command('limpiar_datos_invalidos', stdout=buffer)

        buffer.write("\n🔎 Verificando asistencias inválidas:\n")
        call_command('limpiar_asistencias_invalidas', stdout=buffer)

        buffer.write("\n🔎 Verificando inconsistencias generales:\n")
        call_command('detectar_inconsistencias', stdout=buffer)

        contenido = buffer.getvalue()

        send_mail(
            subject="📊 Informe de Mantenimiento - Sistema Jardines",
            message=contenido,
            from_email="notificaciones@sistema-jardines.com",
            recipient_list=["tudireccion@email.com"],
        )
