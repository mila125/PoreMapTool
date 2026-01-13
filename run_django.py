import os
import sys
import webbrowser
from threading import Timer
from django.core.management import execute_from_command_line

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "mi_proyecto.settings"
)

def open_browser():
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    Timer(2, open_browser).start()
    execute_from_command_line([
        sys.argv[0],
        "runserver",
        "127.0.0.1:8000"
    ])
