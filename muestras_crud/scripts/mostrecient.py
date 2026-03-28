# mostrecient.py
import os
from datetime import datetime

def get_most_recent_report(folder="reports"):
    """
    Busca el archivo más reciente en la carpeta especificada.
    Devuelve la ruta completa al archivo o None si no hay archivos.
    """
    if not os.path.exists(folder):
        print(f" La carpeta '{folder}' no existe.")
        return None

    archivos = [
        os.path.join(folder, f) for f in os.listdir(folder)
        if os.path.isfile(os.path.join(folder, f))
    ]

    if not archivos:
        print(f" No hay archivos en '{folder}'.")
        return None

    archivo_mas_reciente = max(archivos, key=os.path.getmtime)
    fecha = datetime.fromtimestamp(os.path.getmtime(archivo_mas_reciente))

    print(f" Archivo más reciente: {archivo_mas_reciente} (modificado {fecha})")
    return archivo_mas_reciente


if __name__ == "__main__":
    # Para pruebas directas
    get_most_recent_report()