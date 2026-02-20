from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from users.decorators import solo_coordinador

from jardines.models import Programa
from alumnos.models import Inscripcion
from .models import RespuestaFormulario, EstructuraFormulario, CampoFormulario
from .forms import EstructuraFormularioForm, CampoFormularioForm, FormularioDinamico

@login_required
@solo_coordinador
def lista_estructuras(request):
    estructuras = EstructuraFormulario.objects.select_related("programa")
    return render(request, "formularios/lista_estructuras.html", {
        "estructuras": estructuras
    })

@login_required
@solo_coordinador
def crear_estructura(request):

    if request.method == "POST":
        form = EstructuraFormularioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("formularios:lista_estructuras")
    else:
        form = EstructuraFormularioForm()

    return render(request, "formularios/crear_estructura.html", {
        "form": form
    })

@login_required
@solo_coordinador
def detalle_estructura(request, estructura_id):
    estructura = get_object_or_404(EstructuraFormulario, id=estructura_id)

    campos = estructura.campos.all()

    return render(request, "formularios/detalle_estructura.html", {
        "estructura": estructura,
        "campos": campos
    })

@login_required
@solo_coordinador
def crear_campo(request, estructura_id):

    estructura = get_object_or_404(EstructuraFormulario, id=estructura_id)

    if request.method == "POST":
        form = CampoFormularioForm(request.POST)
        if form.is_valid():
            campo = form.save(commit=False)
            campo.estructura = estructura
            campo.save()
            return redirect("formularios:detalle_estructura", estructura_id=estructura.id)
    else:
        form = CampoFormularioForm()

    return render(request, "formularios/crear_campo.html", {
        "form": form,
        "estructura": estructura
    })


@login_required
def responder_formulario(request, inscripcion_id):
    inscripcion = get_object_or_404(Inscripcion, id=inscripcion_id)
    programa = inscripcion.programa
    
    # Verificar si el programa tiene estructura de formulario activa
    try:
        estructura = programa.estructura_formulario
        if not estructura.activo:
            # Si no está activo, redirigir a donde corresponda (detalle alumno/inscripción)
            # Por ahora un simple render o redirect placeholder
            return redirect("formularios:respuesta_exitosa") # Placeholder
    except EstructuraFormulario.DoesNotExist:
        return redirect("formularios:respuesta_exitosa") # Placeholder

    # Verificar permisos (solo docente asignado o coordinador/admin)
    # TODO: Refinar permisos. Por ahora asumimos que si puede ver la inscripción, puede llenar el form.
    
    if request.method == "POST":
        form = FormularioDinamico(request.POST, estructura=estructura)
        if form.is_valid():
            # Guardamos la respuesta
            RespuestaFormulario.objects.create(
                inscripcion=inscripcion,
                formulario=estructura,
                datos=form.cleaned_data
            )
            return redirect("formularios:respuesta_exitosa")
    else:
        form = FormularioDinamico(estructura=estructura)

    return render(request, "formularios/responder_formulario.html", {
        "form": form,
        "inscripcion": inscripcion,
        "estructura": estructura
    })


@login_required
def respuesta_exitosa(request):
    return render(request, "formularios/exito.html")


