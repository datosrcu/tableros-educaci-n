import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from users.models import Usuario
import openpyxl

file_path = "Locaciones 02. Secretaria de Gestión y Participación Ciudadana.xlsx"
wb = openpyxl.load_workbook(file_path, data_only=True)
sheet = wb['Locaciones']

excel_dnis = {}
for i, row in enumerate(sheet.iter_rows(min_row=2, values_only=True)):
    try:
        val = row[2]
        if not val: continue
        dni = str(int(float(val)))
        
        mayo = row[25] or 0
        junio = row[26] or 0
        julio = row[27] or 0
        
        excel_dnis[dni] = {'mayo': mayo, 'junio': junio, 'julio': julio}
    except Exception as e:
        pass

docentes = Usuario.objects.filter(rol='docente')

matched = []
unmatched = []

for d in docentes:
    dni_db = str(d.dni).strip().replace('.', '').replace(' ', '')
    if not dni_db:
        dni_db = str(d.username).strip().replace('.', '').replace(' ', '')
        
    if dni_db in excel_dnis:
        matched.append((d, excel_dnis[dni_db]))
    else:
        unmatched.append(d)
        
print(f"Loaded {len(excel_dnis)} DNIs from Excel.")
print(f"Total docentes in DB: {docentes.count()}")
print(f"Matched {len(matched)} docentes.")
print(f"Unmatched {len(unmatched)} docentes.")

print("\n--- SAMPLE MATCHES ---")
for d, data in matched[:5]:
    print(f"Docente: {d.get_full_name()} | DNI: {d.dni} | Mayo: {data['mayo']} | Junio: {data['junio']} | Julio: {data['julio']}")
