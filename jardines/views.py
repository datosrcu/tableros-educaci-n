from django.shortcuts import render
from django.http import JsonResponse
from .models import Subprograma, Jardin, Sala

def cargar_subprogramas(request):
    programa_id = request.GET.get("programa_id")
    subprogramas = Subprograma.objects.filter(programa_id=programa_id)

    return JsonResponse(
        [{"id": s.id, "nombre": s.nombre} for s in subprogramas],
        safe=False
    )

def cargar_jardines(request):
    programa_id = request.GET.get("programa_id")
    jardines = Jardin.objects.filter(programa_id=programa_id)

    return JsonResponse(
        [{"id": j.id, "nombre": j.nombre} for j in jardines],
        safe=False
    )

def validar_docente_turno(request):
    docente_id = request.GET.get("docente_id")
    turno = request.GET.get("turno")
    sala_id = request.GET.get("sala_id")

    qs = Sala.objects.filter(docentes__id=docente_id, turno=turno)

    if sala_id:
        qs = qs.exclude(id=sala_id)

    return JsonResponse({"conflicto": qs.exists()})


def subprogramas_por_programa(request):
    programa_id = request.GET.get("programa_id")

    subprogramas = []
    if programa_id:
        subprogramas = list(
            Subprograma.objects.filter(programa_id=programa_id)
            .values("id", "nombre")
        )

    return JsonResponse(subprogramas, safe=False)
# Create your views here.
