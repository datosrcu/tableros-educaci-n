from django.urls import path
from . import views

app_name = "formularios"

urlpatterns = [
    path("", views.lista_estructuras, name="lista_estructuras"),
    path("crear/", views.crear_estructura, name="crear_estructura"),
    path("<int:estructura_id>/", views.detalle_estructura, name="detalle_estructura"),
    path("<int:estructura_id>/campo/nuevo/", views.crear_campo, name="crear_campo"),
    path("responder/<int:inscripcion_id>/", views.responder_formulario, name="responder_formulario"),
    path("exito/", views.respuesta_exitosa, name="respuesta_exitosa"),

]
