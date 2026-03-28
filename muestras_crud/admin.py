# -----------------------------
# admin.py
# -----------------------------
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.http import HttpResponseRedirect, HttpResponse
from django.conf import settings
import os
import pandas as pd
import numpy as np
from .models import Informe, Dataset
from . import utils
from muestras_crud import models
# SOLO DEJA ESTA IMPORTACIÓN
from .models import Dataset, Empresa, Informe
import logging
from django.contrib import admin
from django.contrib.admin import AdminSite
# Define el logger de tu módulo
logger = logging.getLogger(__name__)
# importa modelos
# from .models import Empresa, Muestra, Informe, Dataset # ya estÃ¡n en este archivo compuesto

class CustomAdminSite(AdminSite):
    site_header = "Mi Admin Personalizado"
    site_title = "Mi Admin"
    index_title = "Panel de Control"
    
    class Media:
        css = {
            'all': ('css/custom_admin.css',)  # ruta relativa a staticfiles
        }

# Registrar Empresa
@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
 list_display = ('id', 'nombre', 'encargado')
 search_fields = ('nombre', 'encargado')
 list_per_page = 10



# Dataset admin
# =========================================
# ADMIN DE DATASET
# =========================================

class DatasetAdmin(admin.ModelAdmin):
    list_display = [
     "get_informe_id",
     "informe",
     "single_bet",
     "bjh_pore_volume_avg",
     "hk_volume_cc_g",
     "dft_pore_volume",
     "fhh",
     "nk",
     "volumen_total_porosidad",
     "created_at",
   ]

    ordering = ("-created_at",)

    search_fields = (
        "informe__muestra__sample_number",
        "informe__muestra__empresa__nombre",
    )

    list_filter = ("informe__muestra__empresa",)

    list_per_page = 10

    actions = (
        "descargar_excel",
        "descargar_dataset_completo_excel",
        "borrar_todo_dataset",
        "ver_pca",
    )

    def get_informe_id(self, obj):
        return obj.informe.id
    get_informe_id.short_description = "ID Informe"

    # === Acciones ===
    def ver_pca(self, request, queryset):
        """Redirige a la vista del PCA"""
        return HttpResponseRedirect(reverse("pca_visualizacion"))
    ver_pca.short_description = "Visualizar análisis PCA y K-means"

    def descargar_excel(self, request, queryset):
        """Descargar solo los seleccionados"""
        df = pd.DataFrame(list(queryset.values()))
        if df.empty:
            self.message_user(request, "No hay registros seleccionados para exportar.")
            return HttpResponseRedirect(request.get_full_path())
        df = df.drop(columns=[c for c in ["informe", "created_at"] if c in df.columns], errors='ignore')
        df = df.replace({None: float('nan')})
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = "attachment; filename=dataset_export.xlsx"
        df.to_excel(response, index=False)
        return response
    descargar_excel.short_description = "Descargar selección como Excel"

    def descargar_dataset_completo_excel(self, request, queryset=None):
        """Descargar todo el dataset"""
        df = pd.DataFrame(list(Dataset.objects.all().values()))
        if df.empty:
            self.message_user(request, "El dataset está vacío, no hay nada que exportar.")
            return HttpResponseRedirect(request.get_full_path())
        df = df.drop(columns=[c for c in ["informe", "created_at"] if c in df.columns], errors='ignore')
        df = df.replace({None: float('nan')})
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = "attachment; filename=dataset_completo.xlsx"
        df.to_excel(response, index=False)
        return response
    descargar_dataset_completo_excel.short_description = "Descargar todo el dataset como Excel"

    def borrar_todo_dataset(self, request, queryset=None):
        """Eliminar todos los registros del dataset"""
        count = Dataset.objects.count()
        if count == 0:
            self.message_user(request, "No hay registros para eliminar.")
            return
        Dataset.objects.all().delete()
        self.message_user(request, f"Se han eliminado {count} registros del dataset.")
    borrar_todo_dataset.short_description = "Borrar todo el dataset"

admin.site.register(Dataset, DatasetAdmin)

@admin.register(Informe)
class InformeAdmin(admin.ModelAdmin):
    # Mostrar campos en la lista; multiBET y cell NO editables
    list_display = ("id", "sample_number", "empresa", "archivo_xlsx_link", "archivo_pdf_link", "fecha")
    list_display_links = ("id",)
    actions = ["cargar_informes_a_dataset"]
    list_per_page = 10
    #  AÑADIR ESTE MÉTODO PARA DESHABILITAR EL BOTÓN "AGREGAR INFORME" 
    def has_add_permission(self, request):
        return False
    # ------------------------------------------------------------------

    # Quitar campos editables en la lista
 

    def fecha_creacion(self, obj):
        return obj.created_at
    fecha_creacion.admin_order_field = "created_at"
    fecha_creacion.short_description = "Fecha de creación"
    
    def sample_number(self, obj):
        return obj.muestra.sample_number
    sample_number.admin_order_field = "muestra__sample_number"

    def empresa(self, obj):
        return obj.muestra.empresa.nombre if obj.muestra.empresa else "-"
    empresa.admin_order_field = "muestra__empresa__nombre"

    def archivo_xlsx_link(self, obj):
        if obj.archivo_xlsx:
            return format_html('<a href="{}" target="_blank">Excel</a>', obj.archivo_xlsx.url)
        return "Archivo no encontrado"
    archivo_xlsx_link.short_description = "Archivo Excel"

    def archivo_pdf_link(self, obj):
        if obj.archivo_pdf:
            return format_html('<a href="{}" target="_blank">PDF</a>', obj.archivo_pdf.url)
        return "Archivo no encontrado"
    archivo_pdf_link.short_description = "Archivo PDF"


    @admin.action(description="Cargar informes a Dataset")
    def cargar_informes_a_dataset(self, request, queryset):
        registros_creados = 0

        for inf in queryset:
            Dataset.objects.filter(informe=inf).delete()
            ruta_excel = inf.archivo_xlsx.path if inf.archivo_xlsx else None

            if not ruta_excel:
                self.message_user(request, f"Informe {inf.id} no tiene archivo asociado.", level='warning')
                continue

            try:
                resumen = utils.extraer_bet_area(ruta_excel)
                valores_finales = utils.extraer_datos_porosidad(ruta_excel)
                resultados_calculos = utils.extraer_resultado_calculos(ruta_excel)
                # Eliminar campos que no están en Dataset
                campos_validos = {k: v for k, v in resultados_calculos.items() if k in [f.name for f in Dataset._meta.get_fields()]}

                Dataset.objects.update_or_create(
                  informe=inf,
                  defaults={**resumen, **valores_finales, **campos_validos}
                )
                registros_creados += 1

            except Exception as e_carga:
                self.message_user(
                    request,
                    f"Informe {inf.id}: Error CRÍTICO al procesar el archivo Excel: {e_carga}",
                    level='error'
                )

        self.message_user(
            request,
            f"Carga finalizada. Total de {registros_creados} registros creados y actualizados.",
            level='success'
        )
            
    