from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from jardines.models import Sala, Jardin, Programa
from alumnos.models import Alumno, Asistencia
from .models import AccionAuditoria, Usuario
from .middleware_audit import get_current_user

def log_action(instance, action, description):
    user = get_current_user()
    # Logueamos si el usuario es coordinador, admin o docente (para sus propias acciones)
    if user and (user.es_coordinador() or user.es_admin() or user.es_docente()):
        try:
            # Verificamos que el usuario aún exista en la DB (evita IntegrityError en tests)
            if Usuario.objects.filter(pk=user.pk).exists():
                AccionAuditoria.objects.create(
                    usuario=user,
                    accion=action,
                    modelo=instance.__class__.__name__,
                    objeto_id=instance.pk,
                    descripcion=description
                )
        except Exception:
            # En caso de error (ej: DB no accesible), fallamos silenciosamente para no romper la app
            pass

@receiver(post_save, sender=Sala)
def log_sala_save(sender, instance, created, **kwargs):
    action = "creacion" if created else "modificacion"
    desc = f"{'Creada' if created else 'Modificada'} la sala '{instance.nombre}' en el jardín '{instance.jardin.nombre}'"
    log_action(instance, action, desc)

@receiver(post_delete, sender=Sala)
def log_sala_delete(sender, instance, **kwargs):
    desc = f"Eliminada la sala '{instance.nombre}' del jardín '{instance.jardin.nombre}'"
    log_action(instance, "eliminacion", desc)

@receiver(post_save, sender=Jardin)
def log_jardin_save(sender, instance, created, **kwargs):
    action = "creacion" if created else "modificacion"
    desc = f"{'Creado' if created else 'Modificado'} el espacio '{instance.nombre}' ({instance.sector})"
    log_action(instance, action, desc)

@receiver(post_delete, sender=Jardin)
def log_jardin_delete(sender, instance, **kwargs):
    desc = f"Eliminado el espacio '{instance.nombre}'"
    log_action(instance, "eliminacion", desc)

@receiver(post_save, sender=Programa)
def log_programa_save(sender, instance, created, **kwargs):
    action = "creacion" if created else "modificacion"
    desc = f"{'Creado' if created else 'Modificado'} el programa '{instance.nombre}'"
    log_action(instance, action, desc)

@receiver(post_delete, sender=Programa)
def log_programa_delete(sender, instance, **kwargs):
    desc = f"Eliminado el programa '{instance.nombre}'"
    log_action(instance, "eliminacion", desc)

@receiver(m2m_changed, sender=Sala.docentes.through)
def log_docente_asignacion(sender, instance, action, pk_set, reverse, **kwargs):
    if action in ["post_add", "post_remove"]:
        is_add = action == "post_add"
        
        if reverse:
            # La acción se originó desde Usuario.salas_asignadas.add(sala)
            usuario = instance
            salas = Sala.objects.filter(pk__in=pk_set)
            for sala in salas:
                desc = f"{'Asignado' if is_add else 'Retirado'} docente {usuario.first_name} {usuario.last_name} {'a' if is_add else 'de'} la sala '{sala.nombre}'"
                log_action(sala, "asignacion", desc)
        else:
            # La acción se originó desde Sala.docentes.add(usuario)
            sala = instance
            docentes = Usuario.objects.filter(pk__in=pk_set)
            nombres = ", ".join([f"{u.first_name} {u.last_name}" for u in docentes])
            desc = f"{'Asignados' if is_add else 'Retirados'} docentes [{nombres}] {'a' if is_add else 'de'} la sala '{sala.nombre}'"
            log_action(sala, "asignacion", desc)

# --- Señales para Docentes ---

@receiver(post_save, sender=Alumno)
def log_alumno_save(sender, instance, created, **kwargs):
    action = "creacion" if created else "modificacion"
    desc = f"{'Registrado' if created else 'Actualizado'} el alumno {instance.apellido}, {instance.nombre} (DNI: {instance.dni})"
    log_action(instance, action, desc)

@receiver(post_delete, sender=Alumno)
def log_alumno_delete(sender, instance, **kwargs):
    desc = f"Eliminado del sistema el alumno {instance.apellido}, {instance.nombre} (DNI: {instance.dni})"
    log_action(instance, "eliminacion", desc)

@receiver(post_save, sender=Asistencia)
def log_asistencia_save(sender, instance, created, **kwargs):
    action = "creacion" if created else "modificacion"
    desc = f"{'Cargada' if created else 'Modificada'} asistencia para {instance.alumno.apellido}, {instance.alumno.nombre} el día {instance.fecha.strftime('%d/%m/%Y')} como '{instance.get_estado_display()}'"
    log_action(instance, action, desc)

# --- Señales de Sesión ---
from django.contrib.auth.signals import user_logged_in, user_logged_out

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    # Log de auditoría estándar
    if user.rol in ["coordinador", "administrador", "docente", "auxiliar"]:
        AccionAuditoria.objects.create(
            usuario=user,
            accion="creacion",
            modelo="Sesión",
            objeto_id=user.pk,
            descripcion=f"Inicio de sesión exitoso desde IP: {request.META.get('REMOTE_ADDR')}"
        )
    
    # Registro automático de asistencia (docentes con salas asignadas, auxiliares omitidos si no tienen salas)
    if user.rol in ("docente", "auxiliar") and user.salas_asignadas.exists():
        from jardines.models import inicializar_asistencia_diaria
        inicializar_asistencia_diaria(user, request)


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user and user.rol in ["coordinador", "administrador", "docente", "auxiliar"]:
        AccionAuditoria.objects.create(
            usuario=user,
            accion="eliminacion", # Representa "cierre"
            modelo="Sesión",
            objeto_id=user.pk,
            descripcion=f"Cierre de sesión"
        )
