def salas_docente(usuario):
    if usuario.rol != "docente":
        return None
    return usuario.salas_asignadas.all()
