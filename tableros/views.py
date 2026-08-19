import json
import calendar
from datetime import date, datetime
from django.views.generic import TemplateView
from django.views.decorators.clickjacking import xframe_options_exempt
from django.utils.decorators import method_decorator
from django.db.models import Q, Count
from .models import Programa, Subprograma, Jardin, Sala, Usuario, Alumno, AsignacionSala, Asistencia
from .costos_api import obtener_costos_docentes_api

class IndexView(TemplateView):
    template_name = "tableros/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tableros'] = [
            {
                'id': 'espacios-ludicos',
                'nombre': 'Espacios Lúdicos y de Aprendizaje para la Primera Infancia',
                'subtitulo': 'Jardines Maternales Municipales y Salas Cuna.',
                'url_name': 'tableros:espacios_ludicos',
                'icono': 'fa-child-reaching',
                'color': '#009de0',
            },
            {
                'id': 'alfabetizacion',
                'nombre': 'Programa Municipal de Alfabetización y Acompañamiento Educativo',
                'subtitulo': 'Centros de alfabetización y apoyo escolar en el territorio.',
                'url_name': 'tableros:alfabetizacion',
                'icono': 'fa-book-open-reader',
                'color': '#28a745',
            },
            {
                'id': 'carpinteria',
                'nombre': 'Escuela Municipal de Carpintería',
                'subtitulo': 'Formación en oficios y producción técnica educativa.',
                'url_name': 'tableros:carpinteria',
                'icono': 'fa-ruler-combined',
                'color': '#fd7e14',
            },
            {
                'id': 'artes-plasticas',
                'nombre': 'Escuela Municipal de Artes Plásticas Manuel Belgrano',
                'subtitulo': 'Talleres artísticos y expresión plástica comunitaria.',
                'url_name': 'tableros:artes_plasticas',
                'icono': 'fa-palette',
                'color': '#6f42c1',
            },
            {
                'id': 'expresion-cultural',
                'nombre': 'Programa Expresión Cultural',
                'subtitulo': 'Desarrollo cultural territorial y participación social.',
                'url_name': 'tableros:expresion_cultural',
                'icono': 'fa-icons',
                'color': '#e83e8c',
            },
        ]
        return context

@method_decorator(xframe_options_exempt, name='dispatch')
class BaseDashboardProgramaView(TemplateView):
    template_name = "tableros/dashboard_espacios_ludicos.html"
    programa_id = None
    programa_nombre = None
    programa_titulo = ""
    programa_subtitulo = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener Objeto Programa
        programa_obj = None
        if self.programa_id:
            programa_obj = Programa.objects.filter(pk=self.programa_id).first()
        elif self.programa_nombre:
            programa_obj = Programa.objects.filter(nombre=self.programa_nombre).first()
        
        if not programa_obj and self.programa_nombre:
            programa_obj = Programa.objects.filter(nombre__icontains=self.programa_nombre).first()

        # Filtros
        subprograma_id = self.request.GET.get('subprograma')
        zona_filtro = self.request.GET.get('zona')
        fecha_filtro = self.request.GET.get('fecha')
        
        # Procesar Fecha
        hoy = date.today()
        meses_es = {
            1: 'ENERO', 2: 'FEBRERO', 3: 'MARZO', 4: 'ABRIL', 
            5: 'MAYO', 6: 'JUNIO', 7: 'JULIO', 8: 'AGOSTO', 
            9: 'SEPTIEMBRE', 10: 'OCTUBRE', 11: 'NOVIEMBRE', 12: 'DICIEMBRE'
        }
        
        if fecha_filtro:
            try:
                filtro_year, filtro_month = map(int, fecha_filtro.split('-'))
                target_date = date(filtro_year, filtro_month, 1)
                mes_label = f"{meses_es[filtro_month]} {filtro_year}"
            except ValueError:
                target_date = hoy.replace(day=1)
                mes_label = f"{meses_es[hoy.month]} {hoy.year}"
        else:
            target_date = hoy.replace(day=1)
            mes_label = f"{meses_es[hoy.month]} {hoy.year}"
            
        start_of_selected_month = target_date
        end_of_selected_month = target_date.replace(day=calendar.monthrange(target_date.year, target_date.month)[1])
        
        # Costos docentes API
        costos_docentes = obtener_costos_docentes_api(target_date)
        
        q_activo_mes = Q(
            Q(fecha_ingreso__lte=end_of_selected_month) | Q(alumno__asistencias__fecha__lte=end_of_selected_month)
        ) & ~Q(
            activo=False,
            fecha_baja__lt=start_of_selected_month
        )
        
        q_baja_mes = Q(
            activo=False, 
            fecha_baja__gte=start_of_selected_month, 
            fecha_baja__lte=end_of_selected_month
        )
        
        if programa_obj:
            jardines = Jardin.objects.filter(programa=programa_obj)
        else:
            jardines = Jardin.objects.all()
            
        if subprograma_id:
            jardines = jardines.filter(subprograma_id=subprograma_id)
        if zona_filtro:
            jardines = jardines.filter(sector=zona_filtro)
            
        jardines_ids = jardines.values_list('id', flat=True)
        
        asignaciones = AsignacionSala.objects.filter(sala__jardin_id__in=jardines_ids)
        
        q_inscriptos = Q(fecha_ingreso__lte=end_of_selected_month) | Q(alumno__asistencias__fecha__lte=end_of_selected_month)
        total_inscriptos = asignaciones.filter(q_inscriptos).values('alumno').distinct().count()
        activos = asignaciones.filter(q_activo_mes).values('alumno').distinct().count()
        bajas = asignaciones.filter(q_baja_mes).values('alumno').distinct().count()
        
        cantidad_espacios = jardines.count()
        
        # Docentes
        docentes_qs = Usuario.objects.filter(
            rol__in=["docente", "auxiliar"],
            salas_asignadas__jardin_id__in=jardines_ids
        ).distinct()
        cantidad_docentes = docentes_qs.count()
        
        # Costo Docente
        total_costo_global = sum(costos_docentes.get(str(d.dni), 0) for d in docentes_qs if d.dni)
        total_activos_global = activos
        
        # Tendencia de Crecimiento (últimos 6 meses)
        meses = []
        cantidades = []
        crecimiento = []
        curr_m = target_date.month
        curr_y = target_date.year
        
        for i in range(5, -1, -1):
            m = curr_m - i
            y = curr_y
            while m <= 0:
                m += 12
                y -= 1
            start_m = date(y, m, 1)
            end_m = date(y, m, calendar.monthrange(y, m)[1])
            
            q_mes = Q(Q(fecha_ingreso__lte=end_m) | Q(alumno__asistencias__fecha__lte=end_m)) & ~Q(activo=False, fecha_baja__lt=start_m)
            c = asignaciones.filter(q_mes).values('alumno').distinct().count()
            
            meses.append(f"{meses_es[m][:3]} {y}")
            cantidades.append(c)
            
        for i in range(len(cantidades)):
            if i == 0 or cantidades[i-1] == 0:
                crecimiento.append(0)
            else:
                pct = round(((cantidades[i] - cantidades[i-1]) / cantidades[i-1]) * 100, 1)
                crecimiento.append(pct)
                
        # Distribución por Zonas (Pie chart)
        pie_data = []
        pie_labels = []
        for sec_val, sec_label in Jardin.SECTORES_CHOICES:
            j_sec = jardines.filter(sector=sec_val).values_list('id', flat=True)
            asig_sec = AsignacionSala.objects.filter(sala__jardin_id__in=j_sec).filter(q_activo_mes).values('alumno').distinct().count()
            if asig_sec > 0:
                pie_labels.append(sec_label)
                pie_data.append(asig_sec)
                
        # Mapa Data JSON
        jardines_mapa = []
        for j in jardines:
            if j.latitud and j.longitud:
                asig_j = AsignacionSala.objects.filter(sala__jardin_id=j.id).filter(q_activo_mes).values('alumno').distinct().count()
                jardines_mapa.append({
                    "id": j.id,
                    "nombre": j.nombre,
                    "lat": j.latitud,
                    "lng": j.longitud,
                    "sector": j.get_sector_display(),
                    "activos": asig_j,
                })

        # Estructura de espacios y salas
        espacios_dict = {}
        for j in jardines:
            espacios_dict[j.nombre] = {
                "sector": j.get_sector_display(),
                "activos": AsignacionSala.objects.filter(sala__jardin_id=j.id).filter(q_activo_mes).values('alumno').distinct().count(),
                "salas": [s.nombre for s in j.salas.all()],
            }

        # Matriz mensual de asistencias
        num_days = calendar.monthrange(target_date.year, target_date.month)[1]
        dias_rango = list(range(1, num_days + 1))
        
        asistencias_qs = Asistencia.objects.filter(
            sala__jardin_id__in=jardines_ids,
            fecha__gte=start_of_selected_month,
            fecha__lte=end_of_selected_month,
            presente=True
        ).values('sala__jardin__nombre', 'sala__turno__nombre', 'sala__nombre', 'fecha').annotate(total=Count('id'))
        
        matriz_asistencia = {}
        for a in asistencias_qs:
            j_nombre = a['sala__jardin__nombre']
            t_nombre = a['sala__turno__nombre'] or "Sin Turno"
            s_nombre = a['sala__nombre']
            dia = a['fecha'].day
            
            if j_nombre not in matriz_asistencia:
                matriz_asistencia[j_nombre] = {
                    "dias": {d: 0 for d in dias_rango},
                    "turnos": {}
                }
            if t_nombre not in matriz_asistencia[j_nombre]["turnos"]:
                matriz_asistencia[j_nombre]["turnos"][t_nombre] = {
                    "dias": {d: 0 for d in dias_rango},
                    "salas": {}
                }
            if s_nombre not in matriz_asistencia[j_nombre]["turnos"][t_nombre]["salas"]:
                matriz_asistencia[j_nombre]["turnos"][t_nombre]["salas"][s_nombre] = {
                    "dias": {d: 0 for d in dias_rango}
                }
                
            matriz_asistencia[j_nombre]["dias"][dia] += a['total']
            matriz_asistencia[j_nombre]["turnos"][t_nombre]["dias"][dia] += a['total']
            matriz_asistencia[j_nombre]["turnos"][t_nombre]["salas"][s_nombre]["dias"][dia] += a['total']
            
        for j_nombre, j_datos in matriz_asistencia.items():
            j_datos["dias_con_asist"] = sum(1 for d, t in j_datos["dias"].items() if t > 0)
            for t_nombre, t_datos in j_datos["turnos"].items():
                t_datos["dias_con_asist"] = sum(1 for d, t in t_datos["dias"].items() if t > 0)
                for s_nombre, s_datos in t_datos["salas"].items():
                    s_datos["dias_con_asist"] = sum(1 for d, t in s_datos["dias"].items() if t > 0)

        reporte_mensual = [{"espacio": k, **v} for k, v in matriz_asistencia.items()]
        reporte_mensual.sort(key=lambda x: x["espacio"])

        subprog_qs = Subprograma.objects.filter(programa=programa_obj) if programa_obj else Subprograma.objects.all()

        context.update({
            "programa_titulo": self.programa_titulo or (programa_obj.nombre if programa_obj else "Tablero de Gestión Educativa"),
            "programa_subtitulo": self.programa_subtitulo or (f"Dashboard exclusivo de {programa_obj.nombre}" if programa_obj else "Analítica y monitoreo territorial."),
            "total_inscriptos": total_inscriptos,
            "activos": activos,
            "bajas": bajas,
            "cantidad_espacios": cantidad_espacios,
            "cantidad_docentes": cantidad_docentes,
            "costo_total_docentes": total_costo_global,
            "costo_x_alumno_global": (total_costo_global / total_activos_global) if total_activos_global > 0 else 0,
            "mapa_data_json": json.dumps(jardines_mapa),
            "grafico_labels_json": json.dumps(meses),
            "grafico_data_json": json.dumps(cantidades),
            "grafico_crecimiento_json": json.dumps(crecimiento),
            "pie_labels_json": json.dumps(pie_labels),
            "pie_data_json": json.dumps(pie_data),
            "espacios_dict": espacios_dict,
            "reporte_mensual": reporte_mensual,
            "dias_mes": dias_rango,
            "mes_nombre_reporte": mes_label,
            "subprogramas": subprog_qs,
            "subprograma_sel": int(subprograma_id) if subprograma_id and subprograma_id.isdigit() else '',
            "zona_sel": zona_filtro or '',
            "sectores": Jardin.SECTORES_CHOICES,
        })
        return context

class DashboardEspaciosLudicosView(BaseDashboardProgramaView):
    programa_id = 1
    programa_nombre = "Espacios lúdicos y de aprendizaje para la primera infancia"
    programa_titulo = "Espacio educativo para la primera infancia (Jardines Maternales Municipales)"
    programa_subtitulo = "Dashboard exclusivo para la primera infancia."

class DashboardAlfabetizacionView(BaseDashboardProgramaView):
    programa_id = 2
    programa_nombre = "Programa Municipal de Alfabetización y Acompañamiento Educativo"
    programa_titulo = "Programa Municipal de Alfabetización y Acompañamiento Educativo"
    programa_subtitulo = "Dashboard de gestión del Programa Municipal de Alfabetización y Acompañamiento Educativo."

class DashboardCarpinteriaView(BaseDashboardProgramaView):
    programa_id = 3
    programa_nombre = "Escuela de Carpintería"
    programa_titulo = "Escuela Municipal de Carpintería"
    programa_subtitulo = "Dashboard de gestión de la Escuela Municipal de Carpintería."

class DashboardArtesPlasticasView(BaseDashboardProgramaView):
    programa_id = 4
    programa_nombre = "Escuela Municipal de Artes Plásticas Manuel Belgrano"
    programa_titulo = "Escuela Municipal de Artes Plásticas Manuel Belgrano"
    programa_subtitulo = "Dashboard de gestión de la Escuela Municipal de Artes Plásticas Manuel Belgrano."

class DashboardExpresionCulturalView(BaseDashboardProgramaView):
    programa_id = 5
    programa_nombre = "Expresión Cultural"
    programa_titulo = "Programa Expresión Cultural"
    programa_subtitulo = "Dashboard de gestión del Programa Expresión Cultural."
