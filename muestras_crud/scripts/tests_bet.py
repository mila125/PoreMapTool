import json
import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import logging
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
import numpy as np
import pandas as pd
import numpy as np
from scipy.stats import linregress
# from file_utils import wait_for_report_file 

# Configuración del logger
# Se inicializará en el bloque __main__
logger = logging.getLogger(__name__)
def log_resultados_dict(resultados_dict):
    log("===== RESULTADOS BET =====")

    for key, value in resultados_dict.items():
        if isinstance(value, dict):
            log(f"{key}:")
            for subkey, subval in value.items():
                log(f"  - {subkey}: {subval}")
        else:
            log(f"{key}: {value}")

    log("===== FIN RESULTADOS =====")
# ---------------- Funciones BET ----------------
def log(msg, level="info"):
    # 1. Imprimir en consola (Salida al CMD/Terminal)
    print(f"[{level.upper()}] {msg}", flush=True) 
    
    # 2. Escribir en el archivo de log (Lógica de logging)
    logger = logging.getLogger()
    
    # Mapeo de niveles para asegurar el llamado correcto y el filtrado.
    level_map = {
        "debug": logger.debug,
        "info": logger.info,
        "warn": logger.warning,
        "error": logger.error,
        "critical": logger.critical
    }
    
    log_method = level_map.get(level.lower(), logger.info)
    log_method(msg)
    
    # 3. CRÍTICO: Forzar el volcado de los logs del archivo
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            handler.flush()
from pathlib import Path
from openpyxl import load_workbook

def _format_valor(v, decimales=6):
    if v is None or pd.isna(v):
        return np.nan
    return round(float(v), decimales)

def calcular_fractales_singlebet_bet(ruta_excel, mostrar_grafica=False):
    """
    Calcula:
    - Número fractal FHH (hoja FHHA)
    - Número fractal NK (hoja NKA)
    - Área superficial SingleBET y desviación estándar del ajuste BET (hoja BET)
    Devuelve los resultados como un diccionario.
    """


    xl = pd.ExcelFile(ruta_excel)
    resultados = {}

    # -----------------------------
    # 1. FHH
    # -----------------------------
    if 'FHHA' in xl.sheet_names:
        df_fhh = pd.read_excel(xl, sheet_name='FHHA')
        df_fhh.columns = df_fhh.columns.str.strip()

        col_pp = [c for c in df_fhh.columns if 'log(log(P/Po))' in c]
        col_vads = [c for c in df_fhh.columns if 'log(Vads)' in c]

        if col_pp and col_vads:
            X = df_fhh[col_pp[0]].values
            Y = df_fhh[col_vads[0]].values
            mask = (X > -1.60) & (X < -0.75)
            X_lin, Y_lin = X[mask], Y[mask]
            slope, _, _, _, _ = linregress(X_lin, Y_lin)
            resultados['FHH'] = slope + 3
        else:
            resultados['FHH'] = np.nan
    else:
        resultados['FHH'] = np.nan

    # -----------------------------
    # 2. NK
    # -----------------------------
    # -----------------------------
    # 2. NK (geométrico – CORREGIDO)
    # -----------------------------
    if 'NKA' in xl.sheet_names:
        df_nk = pd.read_excel(xl, sheet_name='NKA')
        df_nk.columns = df_nk.columns.str.strip()

        # Normalizar nombre mal escrito
        df_nk.rename(columns={
            'Vapor-Liquid Intrface Area': 'area',
            'Radius of curvature': 'radius'
        }, inplace=True)

        # Convertir a numérico (notación científica OK)
        df_nk['radius'] = pd.to_numeric(df_nk['radius'], errors='coerce')
        df_nk['area'] = pd.to_numeric(df_nk['area'], errors='coerce')

        # Eliminar basura física
        df_nk = df_nk.dropna()
        df_nk = df_nk[(df_nk['area'] > 0) & (df_nk['radius'] > 0)]

        # RANGO NK CORRECTO
        df_nk = df_nk[(df_nk['radius'] > 10) & (df_nk['radius'] < 300)]

        if len(df_nk) >= 3:
            log_r = np.log(df_nk['radius'])
            log_A = np.log(df_nk['area'])

            slope, _, r, _, _ = linregress(log_r, log_A)
            resultados['NK'] = 2 - slope
            resultados['NK_R2'] = r**2

            log(f"NK calculado: Df={resultados['NK']:.4f}, R²={r**2:.4f}")
        else:
            log("NK no calculable: puntos insuficientes tras limpieza", "warn")
            resultados['NK'] = np.nan
    else:
        resultados['NK'] = np.nan
        # -----------------------------
        # 3. SingleBET y desviación estándar
        # -----------------------------
    if 'BET' in xl.sheet_names:
        df_bet = pd.read_excel(xl, sheet_name='BET')
        df_bet.columns = df_bet.columns.str.strip()

        # Forzar columnas críticas a tipo float
        df_bet['Volume @ STP'] = pd.to_numeric(df_bet['Volume @ STP'].astype(str).str.replace(',', '.'), errors='coerce')
        pressure_col = get_pressure_column(df_bet)  # columna de presión limpia y convertida
        df_bet[pressure_col] = pd.to_numeric(df_bet[pressure_col].astype(str).str.replace(',', '.'), errors='coerce')

        # Eliminar filas con NaN en columnas críticas
        df_bet.dropna(subset=['Volume @ STP', pressure_col], inplace=True)

        try:
            mask = (df_bet[pressure_col] >= 0.05) & (df_bet[pressure_col] <= 0.35)
            X = df_bet.loc[mask, pressure_col].values
            Y = df_bet.loc[mask, 'Volume @ STP'].values

            # Cálculo SingleBET
            f = X / (Y * (1 - X))
            slope, intercept, _, _, _ = linregress(X, f)
            single_bet = 1 / (intercept * 4.35)
            f_pred = intercept + slope * X
            bet_sd = np.sqrt(np.sum((f - f_pred) ** 2) / (len(X) - 2))

            resultados['SingleBET'] = single_bet
            resultados['BET_SD'] = bet_sd

        except Exception as e:
            log(f"Error calculando SingleBET: {e}", "error")
            resultados['SingleBET'] = np.nan
            resultados['BET_SD'] = np.nan
    else:
        resultados['SingleBET'] = np.nan
        resultados['BET_SD'] = np.nan

    return resultados
def get_pressure_column(df):
    """Detecta la columna de presión relativa aunque el encabezado varíe."""
    posibles = ["Relative Pressure", "P/Po", "P/P0", "Pressure P/Po", "Pressure"]
    
    normalized_cols = {col.lower().replace(" ", ""): col for col in df.columns}
    
    for cand in posibles:
        normalized_cand = cand.lower().replace(" ", "")
        if normalized_cand in normalized_cols:
            col = normalized_cols[normalized_cand]
            
            # --- CORRECCIÓN CRÍTICA AQUÍ: Forzar la columna de presión a float.
            df[col] = pd.to_numeric(df[col], errors="coerce") 
            # Eliminar las filas donde la presión sea NaN, ya que no se pueden comparar
            df.dropna(subset=[col], inplace=True)
            # --- FIN DE CORRECCIÓN CRÍTICA
            
            log(f"Columna de presión relativa detectada: '{col}'")
            return col
    
    error_msg = f"No se encontró columna de presión relativa en {df.columns.tolist()}"
    logger.error(error_msg)
    raise KeyError(error_msg)

def convertir_a_numerico(df):
    """
    Intenta convertir todas las columnas a valores numéricos, 
    forzando la coerción y limpiando los NaN resultantes.
    """
    log("Intentando convertir columnas a tipo numérico con coerción forzada...")
    
    # Lista de columnas que deben ser estrictamente numéricas para los cálculos
    columnas_criticas = ["Volume @ STP"] # 'Volume @ STP' es vital, la de presión se limpia en get_pressure_column
    
    # Forzar la conversión de todas las columnas (texto -> NaN)
    for col in df.columns:
        # Usamos errors='coerce' para convertir cualquier texto no numérico a NaN.
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    # Detectar la columna de presión para la limpieza combinada
    col_presion = None
    try:
        # get_pressure_column devuelve el nombre de la columna, pero también hace su propia limpieza
        # Aquí la llamamos solo para obtener el nombre de la columna para el dropna final.
        # Ya que llamarla dos veces puede ser ineficiente, es mejor identificarla manualmente si es posible.
        
        posibles = ["Relative Pressure", "P/Po", "P/P0", "Pressure P/Po", "Pressure"]
        normalized_cols = {col.lower().replace(" ", ""): col for col in df.columns}
        for cand in posibles:
            if cand.lower().replace(" ", "") in normalized_cols:
                col_presion = normalized_cols[cand.lower().replace(" ", "")]
                columnas_criticas.append(col_presion)
                break
    except Exception:
        pass # Si falla la detección, asumimos que no hay columna de presión detectable.

    #  CRÍTICO: Eliminar filas donde las columnas críticas no pudieron convertirse (eran texto)
    if col_presion:
        log(f"Eliminando filas con NaN en: {columnas_criticas}")
        df.dropna(subset=columnas_criticas, inplace=True)
    
    return df
# ---------------- Funciones BET revisadas ----------------


def clasificar_poros_dft(ruta_excel: str, hoja: str = "DFT", dividir_dV_por_10: bool = True) -> dict:
    """
    Procesa un archivo Excel de DFT y clasifica los poros, sumando dV por tipo.
    Devuelve siempre un diccionario con floats, usando 0.0 cuando no hay datos.

    Parámetros:
    - ruta_excel: ruta al archivo Excel.
    - hoja: nombre de la hoja con los datos DFT.
    - dividir_dV_por_10: si True divide los valores de dV por 10.

    Retorna:
    - Diccionario con suma de dV por tipo de poro.
      Si un tipo no tiene datos, se asigna 0.0.
    """
    TIPOS_PORO = ["Cilíndrico", "Placa", "Cuello de Botella", "No diferenciados", "Microporos"]

    try:
        # Leer Excel
        df = pd.read_excel(ruta_excel, sheet_name=hoja)
        df.columns = df.columns.str.strip()  # quitar espacios

        # Validar columnas críticas
        for col in ["Half pore width Pore Volume", "dV(r)"]:
            if col not in df.columns:
                raise ValueError(f"Falta columna crítica: {col}")

        # Convertir a numérico y eliminar filas inválidas
        df["Half pore width Pore Volume"] = pd.to_numeric(df["Half pore width Pore Volume"], errors="coerce")
        df["dV(r)"] = pd.to_numeric(df["dV(r)"], errors="coerce")
        df.dropna(subset=["Half pore width Pore Volume", "dV(r)"], inplace=True)

        # Clasificación de poros
        def classify_pore(h):
            if 7.5 <= h < 10:
                return "Microporos"
            elif 10 <= h < 18:
                return "No diferenciados"
            elif 18 <= h <= 180:
                return "Placa"
            else:
                return "Fuera de rango"

        df["pore_type"] = df["Half pore width Pore Volume"].apply(classify_pore)


        # Integración de volumen por tipo de poro
        result = (
            df.groupby("pore_type")["dV(r)"]
            .sum()
            .reindex(TIPOS_PORO)
        ).fillna(0.0)  # reemplaza 'nd' por 0.0

        # Convertir a dict con floats
        return result.astype(float).to_dict()

    except Exception as e:
        print(f"[ERROR] procesar_dft: {e}")
        # Diccionario seguro con 0.0 si ocurre error
        return {tipo: 0.0 for tipo in TIPOS_PORO}

def sanitize_dft_poros(poros_dict):
    """
    Convierte todos los valores de DFT_Poros a float, excepto 'Microporos'.
    Los valores 'nd' o no numéricos se transforman en 0.0.
    """
    sanitized = {}
    for tipo, valor in poros_dict.items():
        if tipo == "Microporos":

            # Dejar el valor original intacto
            sanitized[tipo] = valor/1000
        else:
            try:
                sanitized[tipo] = float(valor)
            except (ValueError, TypeError):
                sanitized[tipo] = 0.0
    return sanitized
def calcular_volumenes_por_poro_clasificado(poros_dict):

    if not isinstance(poros_dict, dict):
        raise TypeError(
            f"Se esperaba dict en calcular_volumenes_por_poro_clasificado, "
            f"pero se recibió {type(poros_dict)}"
        )
   
    poros_sanit = sanitize_dft_poros(poros_dict)

    resultados = {}

    resultados["Microporos_1.6-9.7Å"] = _format_valor(
        poros_sanit.get("Microporos", 0.0)
    )

    meso = (
        poros_sanit.get("Cilíndrico", 0.0)
        + poros_sanit.get("Placa", 0.0)
        + poros_sanit.get("Cuello de Botella", 0.0)
    )

    resultados["Mesoporos_7.7-180Å"] = _format_valor(meso)
    resultados["Mesoporos_15-1767Å"] = _format_valor(meso)

    return resultados
def format_dft_poros(poros_dict):
    """
    Convierte los valores de poros_dft a strings con 6 decimales.
    Microporos se divide por 100 si se desea.
    """
    formatted = {}
    for tipo, dv in poros_dict.items():
        if tipo == "Microporos":
            # Ajuste especial: dividir por 100 al imprimir
            formatted[tipo] = f"{(dv/100):.6f}"
        else:
            formatted[tipo] = f"{dv:.6f}"
    return formatted

def clasificar_poros_bjh(ruta_excel):
    df_ads = pd.read_excel(ruta_excel, sheet_name="BJHA")
    df_des = pd.read_excel(ruta_excel, sheet_name="BJHD")

    for df in (df_ads, df_des):
        df.columns = df.columns.str.strip()

        #  NOMBRE REAL DE LA COLUMNA
        df.rename(columns={
            "Radius Area": "radius"
        }, inplace=True)

        df["radius"] = pd.to_numeric(df["radius"], errors="coerce")
        df["dV(r)"] = pd.to_numeric(df["dV(r)"], errors="coerce")

        df.dropna(subset=["radius", "dV(r)"], inplace=True)

    resultados = {
        "Cilíndrico": 0.0,
        "Cuello de Botella": 0.0
    }

    # Asegurar mismo número de puntos
    n = min(len(df_ads), len(df_des))

    for i in range(n):
        r_ads = df_ads.iloc[i]["radius"]
        r_des = df_des.iloc[i]["radius"]
        dv = df_ads.iloc[i]["dV(r)"]

        # Tolerancia instrumental (~1 Å)
        if abs(r_ads - r_des) <= 1.0:
            resultados["Cilíndrico"] += dv
        elif r_ads > r_des:
            resultados["Cuello de Botella"] += dv

    return resultados
def tests_main(ruta_excel_entrada, directorio_salida):
    log(f"Iniciando tests_main para el archivo: {ruta_excel_entrada}")

    try:
        # -------------------------
        # 1. Procesar BET
        # -------------------------
        df_full = pd.read_excel(ruta_excel_entrada, sheet_name="BET")
        df_full = convertir_a_numerico(df_full)

        # Estimación de puntos de absorción/desorción
        data_point_col = 'Data Point Type'
        total_puntos = len(df_full)
        if data_point_col not in df_full.columns:
            log(f"[WARN] Columna '{data_point_col}' no encontrada. Estimando puntos.", "warn")
            num_absorcion = total_puntos // 2
            num_desorcion = total_puntos - num_absorcion
        else:
            num_absorcion = len(df_full[df_full[data_point_col].astype(str).str.upper() == 'A'])
            num_desorcion = len(df_full[df_full[data_point_col].astype(str).str.upper() == 'D'])
        log(f"Puntos detectados: Absorción={num_absorcion}, Desorción={num_desorcion}")

        poros_dft = clasificar_poros_dft(ruta_excel_entrada)
        
        if not isinstance(poros_dft, dict):
         raise RuntimeError(f"clasificar_poros_dft devolvió {type(poros_dft)}")
        
        poros_bjh = clasificar_poros_bjh(ruta_excel_entrada)
        resultados_dict = {}
        resultados_dict["DFT_Poros"] = poros_dft
        resultados_dict["BJH_Poros"] = poros_bjh
        print("Tipos de poros presentes (DFT, en Å) con dV reducido 1/10:")
        poros_dft["Microporos"] = round(poros_dft["Microporos"], 6)
        for tipo, dv in poros_dft.items():
         dv = round(dv, 6)

         print(f"{tipo}: {dv}")  # imprime siempre 6 decimales
 
     
        #poros_dft = sanitize_dft_poros(poros_dft)  # limpieza
        log(f"[DEBUG] poros_dft devuelto (sanitizado): {poros_dft}", "debug")
 
       
        # -------------------------
        # 3. Volúmenes de microporos/mesoporos
        # -------------------------
        try:

            vol_por_rango = calcular_volumenes_por_poro_clasificado(poros_dft)
            log(f"[DEBUG] Volúmenes por tipo de poro calculados: {vol_por_rango}", "debug")
        except Exception as e:
            log(f"[WARN] No se pudo calcular volúmenes por rango: {e}", "warn")
            vol_por_rango = {
                "Microporos_1.6-9.7Å": "nd",
                "Mesoporos_7.7-180Å": "nd",
                "Mesoporos_15-1767Å": "nd"
            }

        # -------------------------
        # 4. Fractales y SingleBET
        # -------------------------
        fractales = calcular_fractales_singlebet_bet(ruta_excel_entrada)

        # -------------------------
        # 5. Resultados finales
        # -------------------------
        resultados_dict.update(fractales)
        resultados_dict["DFT_Poros"] = poros_dft
        resultados_dict["Volumenes_por_rango"] = vol_por_rango  # <--- añadidos aquí
        resultados_dict["nombre_archivo"] = ruta_excel_entrada
        
        log(f"[DEBUG] Claves finales resultados_dict: {list(resultados_dict.keys())}", "debug")
        log("Tests de BET finalizados. Resultados:")
        log_resultados_dict(resultados_dict)
        log(f"[DEBUG FINAL] tipo DFT_Poros: {type(resultados_dict['DFT_Poros'])}", "debug")
        return resultados_dict

    except Exception as e:
        logger.error(f"Error inesperado en tests_main: {e}")
        return None
# ---------------- Ejecutable ----------------

if __name__ == "__main__":
    
    # Obtener el directorio del script (donde se guardarán los resultados)
    # Usamos os.path.abspath(sys.argv[0]) para ser robustos al path de ejecución
    try:
         #sys.argv[0] es la ruta del script ejecutado
         script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    except IndexError:
        # Fallback si no se puede obtener el path del script (ej. en algunos entornos)
        script_dir = os.getcwd() 

    # 1. Configuración del Logging (Guardar en el directorio del script)
    log_path = os.path.join(script_dir, "bet_analysis.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path, mode='w', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    log("Script de análisis BET iniciado.")
    log(f"Directorio de salida de resultados: {script_dir}")
    
    if len(sys.argv) < 2:
        logger.error("Falta argumento. Uso correcto: python test_bet.py archivo_excel.xlsx")
    else:
        archivo_excel = sys.argv[1]
        
        if not os.path.exists(archivo_excel):
            logger.error(f"Archivo no encontrado: {archivo_excel}")
        else:
            # Llamar a tests_main con el archivo de entrada y el directorio de salida (script_dir)
            tests_main(archivo_excel, script_dir)
            
            log(
                "Análisis BET finalizado.")