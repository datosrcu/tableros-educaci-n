import os
import json
import logging
from datetime import date
import requests

logger = logging.getLogger(__name__)

# URL pública o configurada de Google Sheets API
GOOGLE_SHEETS_COSTOS_URL = os.environ.get(
    'GOOGLE_SHEETS_COSTOS_URL', 
    'https://docs.google.com/spreadsheets/d/e/2PACX-1vQ_EXAMPLE/pub?output=json'
)

def obtener_costos_docentes_api(target_date=None):
    """
    Obtiene el diccionario de costos docentes por DNI/CUIL.
    Usa estrategia híbrida: API en tiempo real con fallback a caché local.
    """
    if target_date is None:
        target_date = date.today()

    cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, f'costos_{target_date.strftime("%Y_%m")}.json')

    # Intentar obtener de Google Sheets API
    try:
        response = requests.get(GOOGLE_SHEETS_COSTOS_URL, timeout=5)
        if response.status_code == 200:
            data = response.json()
            costos = {}
            for item in data.get('rows', []):
                dni = str(item.get('dni', '')).strip().replace('.', '').replace('-', '')
                monto = float(item.get('costo_total', 0) or 0)
                if dni:
                    costos[dni] = monto
            
            # Guardar en caché local
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(costos, f, ensure_ascii=False, indent=2)
            
            return costos
    except Exception as e:
        logger.warning(f"Error al consultar Google Sheets API: {e}. Intentando caché local...")

    # Fallback a caché local si existe
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error al leer caché local {cache_file}: {e}")

    return {}
