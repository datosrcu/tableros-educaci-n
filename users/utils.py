def salas_docente(usuario):
    if usuario.rol not in ["docente", "auxiliar"]:
        return None
    return usuario.salas_asignadas.all()
