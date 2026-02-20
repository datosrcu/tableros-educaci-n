import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import Usuario

def create_test_user(username, password, rol, first_name, last_name, dni):
    if Usuario.objects.filter(username=username).exists():
        print(f"Usuario {username} ya existe.")
        return
    
    user = Usuario.objects.create_user(
        username=username,
        password=password,
        rol=rol,
        first_name=first_name,
        last_name=last_name,
        dni=dni,
        email=f"{username}@example.com"
    )
    
    if rol == 'administrador':
        user.is_staff = True
        user.is_superuser = True
    
    user.save()
    print(f"Usuario {username} ({rol}) creado exitosamente.")

if __name__ == "__main__":
    users_to_create = [
        ("admin_test", "Admin123!", "administrador", "Admin", "Prueba", "11111111"),
        ("coord_test", "Coord123!", "coordinador", "Coord", "Prueba", "22222222"),
        ("docente_test", "Docente123!", "docente", "Docente", "Prueba", "33333333"),
    ]
    
    for u in users_to_create:
        create_test_user(*u)
