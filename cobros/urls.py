from django.urls import path
from . import views

app_name = "cobros"

urlpatterns = [
    path("", views.dashboard_cobros, name="dashboard"),
    path("registrar/<int:asignacion_id>/", views.registrar_pago, name="registrar_pago"),
    path("historial/<int:alumno_id>/", views.historial_pagos, name="historial_pagos"),
    path("comprobante/<int:pago_id>/", views.descargar_comprobante, name="descargar_comprobante"),
]
