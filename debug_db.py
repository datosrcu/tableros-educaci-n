import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def check_table_schema():
    print("Checking 'users_usuario' table schema...")
    with connection.cursor() as cursor:
        cursor.execute("DESCRIBE users_usuario;")
        columns = cursor.fetchall()
        print("\nColumns found in 'users_usuario':")
        for col in columns:
            print(f"- {col[0]} ({col[1]})")
        
        has_rol = any(col[0] == 'rol' for col in col)
        if has_rol:
            print("\n✅ OK: 'rol' column exists.")
        else:
            print("\n❌ ERROR: 'rol' column is MISSING.")
            
        cursor.execute("SELECT COUNT(*) FROM django_migrations WHERE app='users';")
        mig_count = cursor.fetchone()[0]
        print(f"\nApplied migrations for 'users': {mig_count}")

if __name__ == "__main__":
    try:
        check_table_schema()
    except Exception as e:
        print(f"Error checking schema: {e}")
