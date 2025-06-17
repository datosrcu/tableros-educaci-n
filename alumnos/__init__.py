from django_cron import CronJobManager
from alumnos.cron import InformeMantenimientoCron

cron_manager = CronJobManager([
    InformeMantenimientoCron,
])
