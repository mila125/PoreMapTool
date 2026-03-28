import os
import sys
import shutil
import django

# ------------------------------
# CONFIGURACIÓN DE DJANGO
# ------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DJANGO_PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../.."))
sys.path.append(DJANGO_PROJECT_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "muestras.settings")
django.setup()

from django.conf import settings
from muestras_crud.models import Empresa, Muestra, Informe


def ruta_relativa_a_media(ruta_abs, subcarpeta="otros"):
    """Convierte ruta absoluta a relativa dentro de MEDIA_ROOT, copiando si está fuera."""
    if not ruta_abs or not os.path.exists(ruta_abs):
        return None
    try:
        return os.path.relpath(ruta_abs, settings.MEDIA_ROOT)
    except ValueError:
        nombre = os.path.basename(ruta_abs)
        destino_dir = os.path.join(settings.MEDIA_ROOT, "informes", subcarpeta)
        os.makedirs(destino_dir, exist_ok=True)
        destino = os.path.join(destino_dir, nombre)
        shutil.copy2(ruta_abs, destino)
        return os.path.relpath(destino, settings.MEDIA_ROOT)


def subir_resultados_a_django(
    empresa_nombre,
    encargado,
    sample_number,
    ruta_xlsx=None,
    ruta_pdf=None,
    degas=0,
    multiBET=0,
    d_nk=0,
):
    """Crea o actualiza Empresa, Muestra e Informe en Django."""
    try:
        empresa, _ = Empresa.objects.get_or_create(
            nombre=empresa_nombre,
            defaults={"encargado": encargado}
        )

        muestra, _ = Muestra.objects.get_or_create(
            empresa=empresa,
            sample_number=sample_number,
            defaults={
                "degas": degas,
                "multiBET": multiBET,
                "d_nk": d_nk,
            }
        )

        muestra.degas = degas or muestra.degas
        muestra.multiBET = multiBET or muestra.multiBET
        muestra.d_nk = d_nk or muestra.d_nk
        muestra.save()

        xlsx_rel = ruta_relativa_a_media(ruta_xlsx, "xlsx") if ruta_xlsx else None
        pdf_rel = ruta_relativa_a_media(ruta_pdf, "pdf") if ruta_pdf else None

        informe, _ = Informe.objects.get_or_create(
            muestra=muestra,
            defaults={
                "archivo_xlsx": xlsx_rel or "",
                "archivo_pdf": pdf_rel or "",
            }
        )

        if xlsx_rel:
            informe.archivo_xlsx.name = xlsx_rel
        if pdf_rel:
            informe.archivo_pdf.name = pdf_rel
        informe.save()

        print(f" Informe subido correctamente a Django: {sample_number}")
        return True

    except Exception as e:
        print(f" Error subiendo informe {sample_number}: {e}")
        return False


if __name__ == "__main__":
    print(f"Django inicializado correctamente desde: {DJANGO_PROJECT_DIR}")
    print("🔍 Verificando acceso a modelos Django...")

    try:
        print(f"Empresas registradas: {Empresa.objects.count()}")
    except Exception as e:
        print(f" Error accediendo a base de datos: {e}")

    # EJEMPLO DE PRUEBA (puedes borrar esto)
    # subir_resultados_a_django(
    #     empresa_nombre="Empresa Test",
    #     encargado="Encargado Test",
    #     sample_number="PAH_01",
    #     ruta_xlsx=r"C:\QCdata\Reports\PAH_report_01.xlsx",
    #     ruta_pdf=r"C:\QCdata\Reports\PAH_report_01.pdf",
    #     degas=2.1,
    #     multiBET=45.6,
    #     d_nk=2.3,
    # )