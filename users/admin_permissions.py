def es_admin(user):
    return user.is_superuser

def es_directivo(user):
    return user.is_authenticated and user.rol == "directivo"

def es_docente(user):
    return user.is_authenticated and user.rol in ("docente", "auxiliar")
