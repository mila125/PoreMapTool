import os
import sys
import io

# Si estamos dentro de PyInstaller sin consola, crea streams falsos
if getattr(sys, 'frozen', False) and sys.stdout is None:
    sys.stdout = io.TextIOWrapper(io.BytesIO(), encoding='utf-8')
if getattr(sys, 'frozen', False) and sys.stderr is None:
    sys.stderr = io.TextIOWrapper(io.BytesIO(), encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'muestras.settings')

from django.core.management import execute_from_command_line

# Ejecutar servidor sin autoreload
execute_from_command_line(['manage.py', 'runserver', '127.0.0.1:8000', '--noreload'])
