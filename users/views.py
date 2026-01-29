from django.shortcuts import render
from django.contrib.auth.models import Group
from django.shortcuts import render, redirect
from .forms import RegistroDocenteForm


def registrar_docente(request):
    if request.method == 'POST':
        form = RegistroDocenteForm(request.POST)
        if form.is_valid():
            usuario = form.save()

            # ✅ Agregar al grupo 'docentes'
            grupo_docentes, creado = Group.objects.get_or_create(name='docentes')
            usuario.groups.add(grupo_docentes)

            login(request, usuario)
            return redirect('alumnos:dashboard')
    else:
        form = RegistroDocenteForm()
        
def admin_redirect(request):
    if request.user.rol == "docente":
        return redirect("alumnos:dashboard_docente")
    return redirect("/admin/")

    return render(request, 'registration/registrar_docente.html', {'form': form})


