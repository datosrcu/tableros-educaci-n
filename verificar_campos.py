from django.apps import apps
from django.db import models

errores = []

for model in apps.get_models():
    for field in model._meta.fields:
        if isinstance(field, (models.CharField, models.EmailField)):
            if not hasattr(field, "max_length") or field.max_length is None:
                errores.append(f"{model.__module__}.{model.__name__}.{field.name} sin max_length o con None")

if errores:
    print("🚨 Problemas encontrados:")
    for e in errores:
        print(" -", e)
else:
    print("✅ Todos los CharField y EmailField tienen max_length válido.")
