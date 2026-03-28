from muestras_crud.models import Dataset
from django.db import transaction

def fix_duplicates():
    print(" Buscando informes con duplicados...")

    informes = {}

    # Agrupar por informe_id
    for ds in Dataset.objects.all().order_by("created_at"):
        informes.setdefault(ds.informe_id, []).append(ds)

    eliminados = 0

    with transaction.atomic():
        for informe_id, registros in informes.items():
            if len(registros) > 1:
                # Mantener el último
                keep = registros[-1]

                # Eliminar todos excepto el último
                for d in registros[:-1]:
                    d.delete()
                    eliminados += 1

    print(f"✔ Limpieza completa. Eliminados {eliminados} duplicados.")