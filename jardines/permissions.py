from django.core.exceptions import PermissionDenied
from jardines.models import Sala

def validar_sala_para_usuario(usuario, sala):
    if usuario.is_superuser:
        return

    if usuario.rol == "docente":
        if not sala.docentes.filter(id=usuario.id).exists():
            raise PermissionDenied
