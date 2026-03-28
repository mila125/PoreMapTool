import logging
import sys
import pathlib
import os
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from visualizaciones import draw_DFT, draw_HK, draw_comparison_bar_chart, draw_BET
from reportlab.platypus import Image, Paragraph, Spacer
from reportlab.platypus import Table
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Spacer
from reportlab.lib import colors
from reportlab.platypus import PageBreak
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
RUTA_FRACTAL = SCRIPT_DIR / "fractal" / "grafico_fractal.png"
RUTA_EXCEL_TABLA = SCRIPT_DIR / "pdftables" / "tables.xlsx"
RUTA_FIRMA = SCRIPT_DIR / "firma" / "firma.png"
RUTA_ANEXOS = SCRIPT_DIR / "anexos" / "anexos.txt"
RUTA_LOGO = SCRIPT_DIR / "pdflogo" / "pdflogo.png"

ANEXO_TXT = os.path.join("pdftables", "anexos.txt")

def agregar_tabla_encabezado(elementos):
    try:
        df = pd.read_excel(
          RUTA_EXCEL_TABLA,
          sheet_name="ENCABEZADO",
          engine="openpyxl"
)
    except Exception as e:
        log(f"No se pudo leer hoja ENCABEZADO: {e}", "error")
        return

    filas = df.values.tolist()

    tabla = Table(filas, colWidths=[150, 350], hAlign="LEFT")
    tabla.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.75, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))

    elementos.append(tabla)
    elementos.append(Spacer(1, 25))


def agregar_tabla_principal(elementos):
    try:
        df = pd.read_excel(RUTA_EXCEL_TABLA, sheet_name="tables", engine="openpyxl", header=None)
    except Exception:
        log("Hoja 'tables' no existe. Se omite tabla principal.", "info")
        return
    if df.empty:
        log("Hoja 'tables' está vacía. Se omite tabla principal.", "warn")
        return

    primeros = df.iloc[0:5, 0].tolist()
    primeros_val = df.iloc[0:5, 1].tolist()
    ultimos = df.iloc[-5:, 0].tolist()
    ultimos_val = df.iloc[-5:, 1].tolist()
    filas = [[primeros[i], primeros_val[i], ultimos[i], ultimos_val[i]] for i in range(5)]

    tabla = Table(filas, colWidths=[120, 150, 150, 150], hAlign='LEFT')
    tabla.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
    ]))
    elementos.append(tabla)
    elementos.append(Spacer(1, 20))

def agregar_tabla_operador(elementos):
    try:
        df = pd.read_excel(RUTA_EXCEL_TABLA, sheet_name="OPERADOR", engine="openpyxl", header=None)
        datos = df.iloc[:,0].dropna().astype(str).tolist()
        if not datos:
            log("Hoja OPERADOR vacía.", "warn")
            return
    except Exception as e:
        log(f"No se pudo leer hoja OPERADOR: {e}", "error")
        return

    estilo_texto = ParagraphStyle(name="TextoOperador", fontName="Helvetica", fontSize=10, leading=14, spaceAfter=3)
    elementos.append(Paragraph(f"<b>Operador del equipo:</b> {datos[0]}", estilo_texto))
    elementos.append(Spacer(1, 6))
    for linea in datos[1:]:
        elementos.append(Paragraph(linea, estilo_texto))
    elementos.append(Spacer(1, 15))

    if os.path.exists(RUTA_FIRMA):
        elementos.append(Image(RUTA_FIRMA, width=160, height=60))
        elementos.append(Spacer(1, 20))
    else:
        log("Imagen de firma no encontrada. Se omite.", "warn")

def agregar_anexos(elementos):
    if not os.path.exists(RUTA_ANEXOS):
        log(f"No se encontró archivo de anexos: {RUTA_ANEXOS}", "warn")
        return
    with open(RUTA_ANEXOS, "r", encoding="utf-8") as f:
        texto = f.read().strip()
    if not texto:
        log("Archivo de anexos está vacío.", "warn")
        return

    estilo_titulo = ParagraphStyle(name="TituloAnexo", fontName="Helvetica-Bold", fontSize=12, spaceAfter=10)
    estilo_texto = ParagraphStyle(name="TextoAnexo", fontName="Helvetica", fontSize=10, leading=14, alignment=TA_LEFT, spaceAfter=6)
    elementos.append(Spacer(1, 30))
    elementos.append(Paragraph("<b>ANEXO: Resultados de análisis BET</b>", estilo_titulo))
    elementos.append(Spacer(1, 10))
    for parrafo in texto.split("\n"):
        if parrafo.strip():
            elementos.append(Paragraph(parrafo.strip(), estilo_texto))
    elementos.append(Spacer(1, 20))
def agregar_tabla_resultado_calculos(elementos, ruta_excel_informe):
    """
    Tabla principal de resultados:
    - Lee SOLO la hoja RESULTADO_CALCULOS
    - No usa peso, degas ni nombre de muestra
    """

    try:
        df_calc = pd.read_excel(
            ruta_excel_informe,
            sheet_name="RESULTADO_CALCULOS",
            engine="openpyxl"
        )
    except Exception as e:
        log(f"No se pudo leer hoja RESULTADO_CALCULOS: {e}", "error")
        return

    if df_calc.empty:
        log("Hoja RESULTADO_CALCULOS vacía.", "warn")
        return

    filas = []

    # Asumimos:
    # Col 0 = Parámetro
    # Col 1 = Valor
    for _, row in df_calc.iterrows():
        parametro = str(row.iloc[0]).strip()
        valor = str(row.iloc[1]).strip()

        if parametro and parametro.lower() != "nan":
            filas.append([parametro, valor])

    if not filas:
        log("No se encontraron filas válidas en RESULTADO_CALCULOS.", "warn")
        return

    tabla = Table(
        filas,
        colWidths=[320, 160],
        hAlign="LEFT"
    )

    tabla.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))

    elementos.append(tabla)
    elementos.append(Spacer(1, 25))
def agregar_tabla_resultado_poros(elementos, ruta_excel_informe):
    """
    Agrega la tabla RESULTADO_POROS desde el Excel del informe
    """
    try:
        df = pd.read_excel(
            ruta_excel_informe,
            sheet_name="RESULTADO_POROS",
            engine="openpyxl"
        )
    except Exception as e:
        log(f"No se pudo leer hoja RESULTADO_POROS: {e}", "warn")
        return

    if df.empty:
        log("Hoja RESULTADO_POROS está vacía.", "warn")
        return

    # Convertir a filas para ReportLab
    filas = [df.columns.tolist()] + df.astype(str).values.tolist()

    num_cols = len(filas[0])
    ancho_total = 500
    col_widths = [ancho_total / num_cols] * num_cols

    tabla = Table(
        filas,
        colWidths=col_widths,
        hAlign="LEFT"
    )

    tabla.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))

    elementos.append(tabla)
    elementos.append(Spacer(1, 20))


def agregar_graficos(doc_elements, graficos, styles,
                     ruta_excel_tabla, ruta_excel_informe,
                     header_image_path=None):

    # --- Logo ---
    if header_image_path and os.path.exists(header_image_path):
        doc_elements.append(Image(header_image_path, width=500, height=80))
        doc_elements.append(Spacer(1, 15))


    # --- TABLA ENCABEZADO (NUEVA) ---
  
    agregar_tabla_encabezado(doc_elements)
    doc_elements.append(Spacer(1, 20))
        # --- Título ---
    doc_elements.append(Paragraph("Informe Técnico", styles['Title']))
    doc_elements.append(Spacer(1, 20))
    #agregar_tabla_principal(doc_elements)
    agregar_tabla_resultado_calculos(doc_elements, ruta_excel_informe)

    agregar_tabla_operador(doc_elements)

    doc_elements.append(Spacer(1, 30))
        # --- ANEXOS ---
    ruta_anexos = os.path.join("anexos", "anexos.txt")
    agregar_anexos(doc_elements)
    # --- Gráficos ---
    # --- Gráficos en formato 2x2 ---

    # ==============================
    # GRÁFICOS DE ISOTERMAS (2x2)
    # ==============================
    imagenes = []

    for nombre, ruta_img in graficos.items():
        if nombre == "Fractal":
            continue
        if ruta_img:
            imagenes.append(Image(ruta_img, width=230, height=160))

    # Agrupar de a 4 (2x2)
    for i in range(0, len(imagenes), 4):
        bloque = imagenes[i:i+4]

        # completar si faltan
        while len(bloque) < 4:
            bloque.append(Spacer(1, 1))

        tabla_imgs = Table(
            [
                bloque[0:2],
                bloque[2:4]
            ],
            colWidths=[250, 250]
        )

        tabla_imgs.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ]))

        doc_elements.append(tabla_imgs)
        doc_elements.append(Spacer(1, 25))

    # --- TABLA RESULTADO_POROS (ANTES DEL FRACTAL) ---
    # =====================================
    # NUEVA PÁGINA: RESULTADO DE POROS
    # =====================================
    doc_elements.append(PageBreak())
    doc_elements.append(Paragraph(
    "<b>Tabla: Resultados de distribución de poros</b>",
    styles["Heading3"]
    ))
    doc_elements.append(Spacer(1, 10))
    # --- TABLA RESULTADO_POROS ---
    agregar_tabla_resultado_poros(doc_elements, ruta_excel_informe)

    # --- FRACTAL (MÁS PEQUEÑO) ---
    if graficos.get("Fractal"):
        doc_elements.append(Spacer(1, 20))
        doc_elements.append(Image(
            graficos["Fractal"],
            width=420,
            height=400
        ))
        doc_elements.append(Spacer(1, 20))
# ------------------------------
# Configuración de logging
# ------------------------------
def setup_logging(log_folder=None, force=True):
    """
    Inicializa el logger raíz con FileHandler y StreamHandler.
    Si no se pasa log_folder, se usa una carpeta 'logs' al lado del script.
    """
    SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
    LOGS_DIR = pathlib.Path(log_folder) if log_folder else SCRIPT_DIR / "logs"
    LOGS_DIR.mkdir(exist_ok=True)
    LOG_FILE = LOGS_DIR / "proceso_novawin.log"

    root = logging.getLogger()
    if force:
        for h in root.handlers[:]:
            root.removeHandler(h)

    root.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s.%(msecs)03d | %(levelname)s | %(name)s | %(message)s",
        "%Y-%m-%d %H:%M:%S"
    )

    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)

    root.addHandler(fh)
    root.addHandler(ch)

    logging.getLogger("PIL").setLevel(logging.WARNING)
    root.info(f"Logging inicializado correctamente. Log file: {LOG_FILE}")
    return LOG_FILE

# ------------------------------
# Función log simplificada
# ------------------------------
def log(msg, level="info"):
    """
    Envía un mensaje al logger raíz configurado.
    """
    logger = logging.getLogger()
    level = level.lower()
    if level == "debug":
        logger.debug(msg)
    elif level in ("warn", "warning"):
        logger.warning(msg)
    elif level == "error":
        logger.error(msg)
    elif level == "critical":
        logger.critical(msg)
    elif level == "success":
        logger.info(f"[SUCCESS] {msg}")
    else:
        logger.info(msg)

def excel_a_pdf(ruta_excel,ruta_frac):
    ruta_excel = pathlib.Path(ruta_excel).resolve()

    """
    Convierte un Excel en un PDF incluyendo gráficos.
    """

    base, _ = os.path.splitext(ruta_excel)
    ruta_pdf = str(base) + ".pdf"
    log(f"No se proporcionó ruta PDF. Se usará: {ruta_pdf}", "info")

    try:
        doc = SimpleDocTemplate(ruta_pdf)
        styles = getSampleStyleSheet()
        elementos = []

        elementos.append(Spacer(1, 20))

        # -------------------------
        # Leer hojas del Excel
        # -------------------------
        hoja_map = {
            "DFT": "DFT",
            "HK": "HK",
            "BJH": "BJHD",
            "BJH_des": "BJHA",
            "BET": "BET"
        }

        dfs = {}
        for key, hoja in hoja_map.items():
            try:
                dfs[key] = pd.read_excel(ruta_excel, sheet_name=hoja, engine="openpyxl")
                if dfs[key].empty:
                    log(f"La hoja '{hoja}' está vacía.", "warn")
            except Exception as e:
                log(f"No se pudo leer la hoja '{hoja}': {e}", "warn")
                dfs[key] = pd.DataFrame()

        # -------------------------
        # Crear gráficos
        # -------------------------
        graficos = {}

        graficos["DFT"] = draw_DFT(dfs["DFT"]) if not dfs["DFT"].empty else None
        graficos["HK"] = draw_HK(dfs["HK"]) if not dfs["HK"].empty else None
        graficos["BJH"] = (
            draw_comparison_bar_chart(dfs["BJH"], dfs["BJH_des"])
            if not dfs["BJH"].empty and not dfs["BJH_des"].empty
            else None
        )
        graficos["BET"] = (
            draw_BET(dfs["BET"])
            if not dfs["BET"].empty and "Volume @ STP" in dfs["BET"].columns
            else None
        )

        if graficos["BET"] is None:
            log("Hoja BET no contiene columna 'Volume @ STP' o está vacía.", "warn")

        # -------------------------
        # FRACTAL (RUTA FIJA)
        # -------------------------
    
        graficos["Fractal"] = str(ruta_frac)
        log(f"Usando imagen Fractal: {ruta_frac}", "info")
       
        # -------------------------
        # Insertar todo al PDF
        # -------------------------
        header_path = str(RUTA_LOGO)

        agregar_graficos(
            elementos,
            graficos,
            styles,
            RUTA_EXCEL_TABLA,
            ruta_excel,
            header_path
        )

        doc.build(elementos)
        log(f"PDF generado correctamente: {ruta_pdf}", "info")
        return ruta_pdf

    except Exception as e:
        log(f"Fallo al generar PDF: {e}", "error")
        return None

# ------------------------------
# Ejecución de prueba si se corre directamente
# ------------------------------
if __name__ == "__main__":
    setup_logging(force=True)
    log("Script iniciado", "info")

    ruta_excel_prueba = "PAH_report_82.xlsx"
    if os.path.exists(ruta_excel_prueba):
        excel_a_pdf(ruta_excel_prueba)
    else:
        log(f"No se encontró el archivo de prueba: {ruta_excel_prueba}", "error")