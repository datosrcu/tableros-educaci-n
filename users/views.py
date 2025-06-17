from django.shortcuts import render

from django.shortcuts import render, redirect
from .forms import RegistroDocenteForm

def registrar_docente(request):
    if request.method == 'POST':
        form = RegistroDocenteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # Redirigimos al login
    else:
        form = RegistroDocenteForm()
    return render(request, 'registration/registrar_docente.html', {'form': form})

# Create your views here.
