import io
import os
from pathlib import Path
import sys
import subprocess
import base64
from io import BytesIO
from datetime import datetime
import logging
logger = logging.getLogger(__name__)
import matplotlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler,RobustScaler
from sklearn.cluster import KMeans
from django.shortcuts import render, get_object_or_404, redirect
from django.http import FileResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files import File
from django.conf import settings
from django.shortcuts import redirect
from muestras_crud.models import Informe, Dataset
import muestras_crud.utils
from .models import Dataset, Muestra, Informe, Empresa
from .forms import MuestraForm, InformeForm
import matplotlib
matplotlib.use("Agg")  # ← CRÍTICO en Django / Windows

import matplotlib.pyplot as plt
# Definimos la ruta de logs de forma absoluta respecto al script
SCRIPT_DIR = Path(__file__).resolve().parent
LOGS_DIR = SCRIPT_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)
LOG_FILE = LOGS_DIR / "proceso_novawin.log"



PDFTABLES_DIR = Path(__file__).resolve().parent / "pdftables"
PDFTABLES_DIR.mkdir(exist_ok=True)

RUTA_TABLES_EXCEL = PDFTABLES_DIR / "tables.xlsx"


QPS_UPLOAD_DIR = os.path.join(settings.MEDIA_ROOT, "qps_uploads")
USUARIO_DE_WINDOWS = 'Administrator' # Cambia esto si es necesario
ESCRITORIO_VM = f"C:\\Users\\{USUARIO_DE_WINDOWS}\\Desktop"
# Ejemplo común: C:\Users\Administrator\Desktop
# muestras_crud/views.py

from django.shortcuts import render
# muestras_crud/views.py

def tutorial_view(request):
    """
    Vista que muestra los pasos a seguir para generar reportes en PoreMap.
    """
    # Debes crear la plantilla 'tutorial.html'
    return render(request, 'tutorial.html', {})
def splash_screen(request):
    """
    Vista para renderizar la pantalla de inicio de PoreMap.
    """
    return render(request, 'splash_poremap.html', {})

def pca_visualizacion(request):
    from django.shortcuts import render
    from .models import Dataset

    import io, base64
    import numpy as np
    import pandas as pd

    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans
    from scipy.stats import ttest_ind

    # =====================================================
    # 1. CARGA DE DATOS
    # =====================================================
    columnas = [
        "bjh_pore_volume_avg",
        "dft_pore_volume",
        "dft_half_pore_width",
        "fhh",
        "hk_volume_cc_g",
        "nk",
        "single_bet",
        "volumen_total_porosidad",
  
    
    ]

    qs = Dataset.objects.all().order_by("informe_id")
    df = pd.DataFrame(list(qs.values(*columnas)))
    df.index = qs.values_list("informe_id", flat=True)

    if df.empty or df.shape[0] < 2:
        return render(request, "admin/pca_visualizacion.html", {
            "error": "No hay suficientes datos para ejecutar PCA."
        })

    # =====================================================
    # 2. LIMPIEZA Y TRANSFORMACIÓN
    # =====================================================
    df = df.select_dtypes(include=[np.number])
    df = df.fillna(df.mean())
    df = df.dropna(how="all")

    original_cols = df.columns.tolist()

    for col in original_cols:
        df[col] = df[col].apply(lambda x: x if x > 0 else 1e-9)
        df[col] = np.log1p(df[col])

    # =====================================================
    # 3. ESCALADO
    # =====================================================
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df)

    # =====================================================
    # 4. PCA (2 COMPONENTES)
    # =====================================================
    pca = PCA(n_components=2, random_state=42)
    X_pca = pca.fit_transform(X_scaled)

    pc1_var, pc2_var = pca.explained_variance_ratio_ * 100

    loadings = pca.components_.T * np.sqrt(pca.explained_variance_)
    loadings_df = pd.DataFrame(loadings, index=original_cols, columns=["PC1", "PC2"])
    loadings_df["magnitude"] = np.sqrt(loadings_df.PC1**2 + loadings_df.PC2**2)

    # =====================================================
    # 5. K-MEANS (DINÁMICO)
    # =====================================================
    n_samples = X_pca.shape[0]
    n_clusters = min(4, n_samples)

    if n_clusters < 2:
        return render(request, "admin/pca_visualizacion.html", {
            "error": "No hay suficientes muestras para clustering."
        })

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X_pca)
    df["cluster"] = clusters

    cluster_to_mineral_base = {
        0: "Zeolita",
        1: "Arcilla",
        2: "Carbón activado",
        3: "Sílice",
    }

    cluster_to_mineral = {
        k: v for k, v in cluster_to_mineral_base.items()
        if k < n_clusters
    }

    df["mineral_microporosidad"] = df["cluster"].map(cluster_to_mineral)

    # Centroides en espacio PCA
    X_pca_df = pd.DataFrame(X_pca, columns=["PC1", "PC2"])
    X_pca_df["cluster"] = clusters
    centroids = X_pca_df.groupby("cluster")[["PC1", "PC2"]].mean().reset_index()
    centroids["mineral"] = centroids["cluster"].map(cluster_to_mineral)

    # =====================================================
    # 6. GRÁFICOS
    # =====================================================
    plots = {}

    def save_plot(fig):
        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", bbox_inches="tight")
        buffer.seek(0)
        img = base64.b64encode(buffer.getvalue()).decode("utf-8")
        plt.close(fig)
        return img

    # --- PCA ---
    fig = plt.figure(figsize=(6, 5))
    plt.scatter(X_pca[:, 0], X_pca[:, 1], alpha=0.6)
    plt.title(f"PCA — PC1 {pc1_var:.2f}% | PC2 {pc2_var:.2f}%")
    plt.xlabel("PC1")
    plt.ylabel("PC2")
    plt.grid(True)
    plots["pca_img"] = save_plot(fig)

    # --- Varianza acumulada ---
    pca_full = PCA()
    pca_full.fit(X_scaled)
    cum_var = np.cumsum(pca_full.explained_variance_ratio_)

    fig = plt.figure(figsize=(6, 5))
    plt.plot(range(1, len(cum_var) + 1), cum_var, marker="o")
    plt.axhline(0.9)
    plt.xlabel("Número de componentes")
    plt.ylabel("Varianza acumulada")
    plt.title("Varianza explicada acumulada")
    plt.grid(True)
    plots["pca_cumulative_variance_img"] = save_plot(fig)

    # --- K-Means + vectores ---
    fig = plt.figure(figsize=(10, 10))
    plt.scatter(X_pca[:, 0], X_pca[:, 1], c=clusters, cmap="viridis", alpha=0.6)

    top_vars = loadings_df.sort_values("magnitude", ascending=False).head(4)
    for var in top_vars.index:
        plt.arrow(
            0, 0,
            top_vars.loc[var, "PC1"] * 0.6,
            top_vars.loc[var, "PC2"] * 0.6,
            head_width=0.08,
            alpha=0.9,
            label=var
        )

    for _, row in centroids.iterrows():
        plt.text(
            row.PC1, row.PC2, row.mineral,
            bbox=dict(facecolor="white", alpha=0.7, edgecolor="none")
        )

    plt.legend()
    plt.title(f"K-Means ({n_clusters} clústeres) sobre PCA")
    plt.xlabel("PC1")
    plt.ylabel("PC2")
    plt.grid(True)
    plots["kmeans_vectors_img"] = save_plot(fig)

    # =====================================================
    # 7. V-TEST (PROTEGIDO)
    # =====================================================
    v_test_results = {}

    if n_samples >= 5:
        for cid in sorted(df.cluster.unique()):
            cluster_data = df[df.cluster == cid][original_cols]
            rest_data = df[df.cluster != cid][original_cols]

            results = []
            for col in original_cols:
                t, p = ttest_ind(cluster_data[col], rest_data[col], equal_var=False)
                results.append({
                    "variable": col,
                    "p_value": f"{p:.3f}",
                    "mean_cluster": f"{cluster_data[col].mean():.3f}",
                    "mean_rest": f"{rest_data[col].mean():.3f}",
                })

            v_test_results[cluster_to_mineral.get(cid, f"Cluster {cid}")] = results
    else:
        v_test_results["Advertencia"] = [{
            "variable": "—",
            "p_value": "—",
            "mean_cluster": "—",
            "mean_rest": "Muestras insuficientes",
        }]

    # =====================================================
    # 8. TEMPLATE
    # =====================================================
    return render(request, "admin/pca_visualizacion.html", {
        "pca_img": plots["pca_img"],
        "kmeans_vectors_img": plots["kmeans_vectors_img"],
        "pc1_var": f"{pc1_var:.2f}",
        "pc2_var": f"{pc2_var:.2f}",
        "clasificacion": df[["mineral_microporosidad"]].to_dict("records"),
        "v_test_results": v_test_results,
    })
def cargar_a_dataset(request, informe_id):

    informe = Informe.objects.get(pk=informe_id)

    # ===============================
    # Validar archivo .xlsx existente
    # ===============================
    ruta_excel = informe.archivo_xlsx.path if informe.archivo_xlsx else None
    if not ruta_excel:
        messages.error(request, f"El informe {informe_id} no tiene archivo Excel asociado.")
        return redirect("admin:muestras_crud_dataset_changelist")

    try:
        xls = pd.ExcelFile(ruta_excel)
    except Exception as e:
        messages.error(request, f"No se pudo abrir el archivo del informe {informe_id}: {e}")
        return redirect("admin:muestras_crud_dataset_changelist")

    # Diccionario donde acumularemos valores finales
    datos_finales = {}

    # ===============================
    # Hojas válidas para extraer datos
    # ===============================
    HOJAS_TABULARES = ['dft', 'hk', 'bjha', 'bjhd', 'resultados_bet']

    for hoja in xls.sheet_names:

        hoja_lower = hoja.lower()

        # Ignorar hojas que no son de datos
        if not any(key in hoja_lower for key in HOJAS_TABULARES):
            continue  

        # Leer hoja
        try:
            df = pd.read_excel(xls, sheet_name=hoja)
        except:
            continue

        if df.empty:
            continue

        # Mapeo para esta hoja
        mapping = muestras_crud.utils.mapear_columnas_excel_a_modelo(df.columns)
        if not mapping:
            continue

        # ===============================
        # TOMAR SOLO EL ÚLTIMO VALOR NO NULO
        # ===============================
        for campo_modelo, col_excel in mapping.items():

            if col_excel not in df.columns:
                continue

            serie = df[col_excel].dropna()

            if not serie.empty:
                valor = muestras_crud.utils.utils.limpiar_valor(serie.iloc[-1])
                datos_finales[campo_modelo] = valor

    # ===============================
    # CREAR O ACTUALIZAR ÚNICO DATASET
    # ===============================
    dataset, created = Dataset.objects.update_or_create(
        informe=informe,
        defaults=datos_finales
    )

    mensaje = "creado" if created else "actualizado"
    messages.success(
        request,
        f"Dataset del informe {informe_id} fue {mensaje} correctamente."
    )

    return redirect("admin:muestras_crud_dataset_changelist")
# --------------------------
# MUESTRAS
# --------------------------

@login_required
def lista_muestras(request):
    muestras = Muestra.objects.select_related('empresa').filter(usuarios_asignados=request.user)
    return render(request, 'muestras/listas.html', {'muestras': muestras})


@login_required
def crear_muestra(request):
    if request.method == 'POST':
        form = MuestraForm(request.POST)
        if form.is_valid():
            muestra = form.save()
            muestra.usuarios_asignados.add(request.user)
            return redirect('lista_muestras')
    else:
        form = MuestraForm()
    return render(request, 'muestras/formulario.html', {'form': form, 'accion': 'Crear'})


@login_required
def editar_muestra(request, id):
    muestra = get_object_or_404(Muestra, id=id, usuarios_asignados=request.user)
    if request.method == 'POST':
        form = MuestraForm(request.POST, instance=muestra)
        if form.is_valid():
            form.save()
            return redirect('lista_muestras')
    else:
        form = MuestraForm(instance=muestra)
    return render(request, 'muestras/formulario.html', {'form': form, 'accion': 'Editar'})


@login_required
def eliminar_muestra(request, id):
    muestra = get_object_or_404(Muestra, id=id, usuarios_asignados=request.user)
    if request.method == 'POST':
        muestra.delete()
        return redirect('lista_muestras')
    return render(request, 'muestras/confirmar_eliminar.html', {'muestra': muestra})


# --------------------------
# INFORMES
# --------------------------

@login_required
def ver_informe(request, muestra_id):
    muestra = get_object_or_404(Muestra, id=muestra_id)
    informe = getattr(muestra, 'informe', None)
    return render(request, 'informes/ver_informe.html', {'muestra': muestra, 'informe': informe})


@login_required
def crear_informe(request, muestra_id):
    muestra = get_object_or_404(Muestra, id=muestra_id)
    if request.method == 'POST':
        form = InformeForm(request.POST, request.FILES)
        if form.is_valid():
            informe = form.save(commit=False)
            informe.muestra = muestra
            informe.save()
            # Generación PDF opcional
            return redirect('ver_informe', muestra_id=muestra.id)
    else:
        form = InformeForm()
    return render(request, 'informes/crear_informe.html', {'form': form, 'muestra': muestra})


@login_required
def listar_informes(request):
    informes = Informe.objects.all()
    return render(request, 'informes/listar_informes.html', {'informes': informes})


# --------------------------
# EJECUCIÓN DE ANÁLISIS
# --------------------------

@login_required
def ejecutar_analisis(request):
    """
    Ejecuta el script externo para todos los informes y guarda archivos XLSX y PDF en cada Informe.
    """
    informes = Informe.objects.all()
    errores = []

    ruta_script = r"C:\Users\6lady\OneDrive\Escritorio\PRACTICAUDEC\python\test\main.py"
    ruta_salida = r"C:\QCdata\Reports"

    for informe in informes:
        try:
            proceso = subprocess.run(
                [sys.executable, ruta_script],
                capture_output=True,
                text=True,
                shell=True
            )

            ruta_pdf = os.path.join(ruta_salida, "reporte.pdf")
            ruta_xlsx = os.path.join(ruta_salida, "PCC_report_06.xlsx")

            if not os.path.exists(ruta_pdf) or not os.path.exists(ruta_xlsx):
                errores.append(f"Informe {informe.id}: archivos no generados")
                continue

            with open(ruta_xlsx, 'rb') as fx:
                informe.archivo_xlsx.save(os.path.basename(ruta_xlsx), File(fx), save=False)
            with open(ruta_pdf, 'rb') as fp:
                informe.archivo_pdf.save(os.path.basename(ruta_pdf), File(fp), save=False)
            informe.save()

        except Exception as e:
            errores.append(f"{informe.id}: {str(e)}")

    if errores:
        messages.warning(request, f" Algunos informes fallaron: {errores}")
    else:
        messages.success(request, " Todos los informes fueron procesados correctamente")

    return redirect('panel_configuracion')


@login_required
def generar_informe_automatico(request, muestra_id):
    """
    Ejecuta el script para una muestra específica.
    """
    muestra = get_object_or_404(Muestra, id=muestra_id)
    ruta_script = r"C:\Users\6lady\OneDrive\Escritorio\PRACTICAUDEC\python\test\main.py"
    ruta_salida = r"C:\QCdata\Reports"

    try:
        proceso = subprocess.run(
            [sys.executable, ruta_script],
            capture_output=True,
            text=True,
            shell=True
        )

        ruta_pdf = os.path.join(ruta_salida, "reporte.pdf")
        ruta_xlsx = os.path.join(ruta_salida, "PCC_report_06.xlsx")

        if not os.path.exists(ruta_pdf) or not os.path.exists(ruta_xlsx):
            return HttpResponse("<h3>No se encontraron archivos generados (.xlsx o .pdf)</h3>")

        informe, _ = Informe.objects.get_or_create(muestra=muestra)

        with open(ruta_xlsx, "rb") as fx:
            informe.archivo_xlsx.save(os.path.basename(ruta_xlsx), File(fx), save=False)
        with open(ruta_pdf, "rb") as fp:
            informe.archivo_pdf.save(os.path.basename(ruta_pdf), File(fp), save=False)

        informe.save()
        return HttpResponse(
            f"<h2> Informe generado correctamente para {muestra.sample_number}</h2>"
            f"<p><a href='{informe.archivo_xlsx.url}'>Descargar Excel</a><br>"
            f"<a href='{informe.archivo_pdf.url}'>Descargar PDF</a></p>"
        )

    except Exception as e:
        return HttpResponse(f"<h2> Error al generar informe:</h2><pre>{str(e)}</pre>")


# --------------------------
# DESCARGA DE ARCHIVOS
# --------------------------

@login_required
def descargar_archivo(request):
    nombre = request.GET.get("file")
    ruta_salida = r"C:\Users\6lady\OneDrive\Escritorio\PRACTICAUDEC\python\test\output"
    ruta_archivo = os.path.join(ruta_salida, nombre)
    if os.path.exists(ruta_archivo):
        return FileResponse(open(ruta_archivo, "rb"), as_attachment=True)
    return HttpResponse("<h3>Archivo no encontrado.</h3>")


@login_required
def descargar_excel(request, muestra_id):
    muestra = get_object_or_404(Muestra, id=muestra_id)
    return FileResponse(open(muestra.informe.archivo_xlsx.path, 'rb'), as_attachment=True, filename=f"{muestra.sample_number}.xlsx")


@login_required
def descargar_pdf(request, muestra_id):
    muestra = get_object_or_404(Muestra, id=muestra_id)
    return FileResponse(open(muestra.informe.archivo_pdf.path, 'rb'), as_attachment=True, filename=f"{muestra.sample_number}.pdf")


# --------------------------
# EMPRESAS Y USUARIOS
# --------------------------

@login_required
def listar_empresas(request):
    empresas = Empresa.objects.all()
    return render(request, 'empresas/listar_empresas.html', {'empresas': empresas})


@login_required
def listar_usuarios(request):
    from django.contrib.auth.models import User
    usuarios = User.objects.all()
    return render(request, 'usuarios/listar_usuarios.html', {'usuarios': usuarios})
def v(x):
    return x if x else "-"
@login_required
def panel_configuracion(request):
    if request.method == "POST":
        # ===============================
        # 1️⃣ DATOS DEL ENCABEZADO
        # ===============================
        def v(x):
            return x.strip() if x else ""

        fecha = request.POST.get("fecha")
        equipo = request.POST.get("equipo")
        analisis = request.POST.get("tipo_analisis")
        tipo_muestras = request.POST.get("tipo_muestra")
        operador = request.POST.get("nombre_operador")
        compania = request.POST.get("nombre_empresa")
        solicitante = request.POST.get("nombre_solicitante")
        orden_trabajo = request.POST.get("orden_trabajo")
        duracion = request.POST.get("duracion_procesamiento", "").strip()

        # ===============================
        # 2️⃣ LISTA DE MUESTRAS
        # ===============================
        muestras = request.POST.getlist("muestra[]")
        pesos = request.POST.getlist("peso[]")
        perdidas = request.POST.getlist("perdidas[]")

        lista_muestras = []
        for i in range(len(muestras)):
            if muestras[i].strip():
                lista_muestras.append({
                    "nombre": muestras[i],
                    "peso": pesos[i],
                    "perdida_gas": perdidas[i]
                })

        operador_nombre = request.POST.get("nombre_operador")
        operador_cargo = request.POST.get("cargo_operador")
        operador_contacto = request.POST.get("contacto_operador")

        # ===============================
        # 3️⃣ DEFINIR RUTAS RELATIVAS
        # ===============================
        SCRIPT_DIR = Path(__file__).resolve().parent
        PDFTABLES_DIR = SCRIPT_DIR / "pdftables"
        PDFTABLES_DIR.mkdir(exist_ok=True)

        RUTA_TABLES_EXCEL = PDFTABLES_DIR / "tables.xlsx"
        RUTA_FIRMA_PNG = PDFTABLES_DIR / "firma.png"
        RUTA_ANEXOS_DIR = PDFTABLES_DIR / "anexos"
        RUTA_ANEXOS_DIR.mkdir(exist_ok=True)

        # ===============================
        # 4️⃣ CREAR DATAFRAMES Y GUARDAR EXCEL
        # ===============================
        df_encabezado = pd.DataFrame({
            "Campo": [
                "Fecha", "Equipo", "Análisis", "Tipo de muestras",
                "Operador", "Duración de procesamiento",
                "Compañía", "Solicitante", "Orden de trabajo"
            ],
            "Valor": [
                v(fecha), v(equipo), v(analisis), v(tipo_muestras),
                v(operador), v(duracion),
                v(compania), v(solicitante), v(orden_trabajo)
            ]
        })

        df_operador = pd.DataFrame({
            "Campo": ["Operador del equipo", "Cargo", "Compañía", "Solicitante", "Orden de trabajo", "Contacto"],
            "Valor": [v(operador_nombre), v(operador_cargo), v(compania), v(solicitante), v(orden_trabajo), v(operador_contacto)]
        })

        with pd.ExcelWriter(RUTA_TABLES_EXCEL, engine="openpyxl") as writer:
            df_encabezado.to_excel(writer, sheet_name="ENCABEZADO", index=False)

            df_operador.to_excel(writer, sheet_name="OPERADOR", index=False)

        messages.success(request, f"Tabla Excel guardada en: {RUTA_TABLES_EXCEL}")

        # ===============================
        # 5️⃣ GUARDAR FIRMA
        # ===============================
        firma = request.FILES.get("firma_png")
        if firma:
            with open(RUTA_FIRMA_PNG, "wb+") as destino:
                for chunk in firma.chunks():
                    destino.write(chunk)
            messages.success(request, f"Firma del operador guardada en: {RUTA_FIRMA_PNG}")
        else:
            messages.info(request, "No se subió firma del operador.")

        # ===============================
        # 6️⃣ GUARDAR ANEXOS
        # ===============================
        archivos_anexo = request.FILES.getlist("archivos_anexo")
        for archivo in archivos_anexo:
            ruta_archivo = RUTA_ANEXOS_DIR / archivo.name
            with open(ruta_archivo, "wb+") as destino:
                for chunk in archivo.chunks():
                    destino.write(chunk)

        if archivos_anexo:
            messages.success(request, f"{len(archivos_anexo)} archivos anexos guardados en: {RUTA_ANEXOS_DIR}")

        # ===============================
        # 7️⃣ VALIDACIONES DE RUTAS
        # ===============================
        path_novawin = request.POST.get("path_novawin", "").strip()
        export_folder = request.POST.get("export_folder", "").strip()
        archivos_qps = request.FILES.getlist("qps_folder_upload")
        path_qps_final = ""

        if archivos_qps:
            try:
                nombre_carpeta_qps = archivos_qps[0].name.split(os.sep)[0]
                ruta_base_guardado = Path(settings.BASE_DIR) / "media" / "qps"
                path_qps_final = ruta_base_guardado / nombre_carpeta_qps
                path_qps_final.mkdir(parents=True, exist_ok=True)

                for archivo_qps in archivos_qps:
                    ruta_archivo_completa = path_qps_final / archivo_qps.name
                    with open(ruta_archivo_completa, "wb+") as destino:
                        for chunk in archivo_qps.chunks():
                            destino.write(chunk)

                messages.success(request, f"Carpeta QPS subida y guardada en: {path_qps_final}")
            except Exception as e:
                messages.error(request, f"Error al guardar QPS: {str(e)}")
                return redirect("panel_configuracion")
        else:
            messages.error(request, "Debe seleccionar una carpeta QPS.")
            return redirect("panel_configuracion")

        if not os.path.exists(path_novawin):
            messages.error(request, f"No se encontró NovaWin en: {path_novawin}")
            return redirect("panel_configuracion")
        if not os.path.exists(export_folder):
            messages.error(request, f"No existe la carpeta de exportación: {export_folder}")
            return redirect("panel_configuracion")

        # ===============================
        # 8️⃣ EJECUTAR SCRIPT EN SEGUNDO PLANO
        # ===============================
        script_path = Path(settings.BASE_DIR) / "muestras_crud" / "scripts" / "main.py"
        log_dir = Path(settings.BASE_DIR) / "logs"
        log_dir.mkdir(exist_ok=True)
        log_file_path = log_dir / "bet_process.log"

        with open(log_file_path, "w", encoding="utf-8") as log_file:
            subprocess.Popen(
                [sys.executable, str(script_path), path_novawin, str(path_qps_final), export_folder],
                stdout=log_file,
                stderr=log_file,
                cwd=str(script_path.parent)
            )

        messages.success(request, "Proceso iniciado correctamente. El análisis se está ejecutando en segundo plano.")
        return redirect("panel_configuracion")

    return render(request, "informes/panel_configuracion.html")

# Determinar la ruta de la carpeta de destino:

def configuracion_ejecucion(request):
    """
    Maneja la subida de la carpeta QPS y guarda los archivos en el Escritorio de la VM.
    """

    if request.method == 'POST':
          # Ahora solo buscamos la carpeta subida
        archivos_qps = request.FILES.getlist('qps_folder_upload')
    
         # ... (El resto de la lógica de guardado en la VM de Windows sigue siendo la misma) ...

        if archivos_qps:
            
            
            ruta_carpeta_final = os.path.join(ESCRITORIO_VM, nombre_carpeta_qps)
    
            #  PUNTO DE COMPROBACIÓN 1: Imprime la ruta
            print(f"--- RUTA DE DESTINO INTENTADA: {ruta_carpeta_final} ---") 
    
            try:
             os.makedirs(ruta_carpeta_final, exist_ok=True)
              # ... (código para guardar archivos) ...

            except Exception as e:
              #  PUNTO DE COMPROBACIÓN 2: Captura el error específico
                print(f"--- ERROR DETALLADO AL ESCRIBIR EN DISCO: {type(e).__name__}: {e} ---")
                   # 1. Obtener el nombre de la carpeta base que el usuario subió
            nombre_carpeta_qps = archivos_qps[0].name.split('/')[0] 

            
            # 2. Definir la ruta de destino completa en el Escritorio de la VM
            ruta_destino_base = ESCRITORIO_VM # 'C:\Users\Administrator\Desktop'
            ruta_carpeta_final = os.path.join(ruta_destino_base, nombre_carpeta_qps)
            
            # Crear la carpeta de destino si no existe
            if not os.path.exists(ruta_carpeta_final):
                os.makedirs(ruta_carpeta_final)
            
            # 3. Guardar cada archivo de la carpeta
            for archivo_qps in archivos_qps:
                # El nombre del archivo en la VM debe ser solo el nombre del archivo, no la ruta relativa
                nombre_archivo = os.path.basename(archivo_qps.name) 
                ruta_archivo_completa = os.path.join(ruta_carpeta_final, nombre_archivo)

                try:
                    # Escribir el contenido del archivo en el disco
                    with open(ruta_archivo_completa, 'wb+') as destination:
                        for chunk in archivo_qps.chunks():
                            destination.write(chunk)
                    # print(f"Guardado: {ruta_archivo_completa}") # Para depuración
                    
                except Exception as e:
                    print(f"Error al guardar {nombre_archivo}: {e}")
                    # messages.error(request, f"Error al guardar los archivos: {e}")
                    return render(request, 'tu_template.html') # Renderiza el formulario con el error

            # 4. Obtener la ruta final (Paso 3: Pasar la ruta de búsqueda)
            # Esta es la ruta que tu script Python posterior usará para procesar los QPS.
            ruta_para_script_qps = ruta_carpeta_final 
            
            # Mensaje de éxito o redirección a la página de resultados/ejecución
            print(f"Carpetas QPS guardada en: {ruta_para_script_qps}")
            # messages.success(request, f"Archivos QPS subidos y guardados en: {ruta_para_script_qps}")

            # Aquí puedes llamar a la función que inicia el análisis con 'ruta_para_script_qps'
            # iniciar_analisis(ruta_para_script_qps, path_novawin, cmultiBET, cell, export_folder)

            return redirect('alguna_otra_vista_o_resultado')

        else:
            # messages.error(request, "No se seleccionó ninguna carpeta QPS.")
            pass # Manejar el caso donde no hay archivos subidos

    # Si es GET o si no hay archivos subidos
    return render(request, "informes/panel_configuracion.html")

