import re
import pandas as pd
import numpy as np

# ============================================================
# 1. LIMPIEZA DE VALORES NUMÉRICOS
# ============================================================
def limpiar_valor(x):
    if pd.isna(x):
        return None
    try:
        x_str = str(x).strip().replace(",", ".")
        x_str = x_str.replace("—", "-")

        match = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", x_str)
        return float(match.group(0)) if match else None
    except Exception:
        return None


# ============================================================
# 2. EXTRAER BET (SINGLE BET)
# ============================================================
def extraer_bet_area(ruta_excel):
    """
    Devuelve SOLO el valor Single BET (área superficial).
    """
    try:
        df = pd.read_excel(ruta_excel, sheet_name="RESULTADOS_BET")

        valores = [
            limpiar_valor(v)
            for v in df.values.flatten()
            if limpiar_valor(v) is not None
        ]

        return {"single_bet": valores[-1] if valores else None}

    except Exception as e:
        print(f"ERROR en extraer_bet_area: {e}")
        return {"single_bet": None}


# ============================================================
# 3. MAPEOS POR HOJA
# ============================================================
MAPPING_HOJA = {
    "BJHA": {"bjha_pore_volume": [r"Pore\s*Volume"]},
    "BJHD": {"bjhd_pore_volume": [r"Pore\s*Volume"]},
    "HK": {"hk_volume_cc_g": [r"Half\s*Pore\s*Width"]},
    "DFT": {
        "dft_pore_volume": [r"Pore\s*Volume"],
        "dft_half_pore_width": [r"Half\s*Pore\s*Width"],
    },
    "FHHA": {"fhh": [r"log\s*\(\s*log\s*\(P/Po\)\s*\)"]},
    "NKA": {"nk": [r"Radius"]},
}


def mapear_columnas_por_hoja(nombre_hoja, columnas_df):
    nombre_hoja = nombre_hoja.upper()
    if nombre_hoja not in MAPPING_HOJA:
        return {}

    patrones = MAPPING_HOJA[nombre_hoja]
    mapeo = {}

    for campo, lista_patrones in patrones.items():
        for patron in lista_patrones:
            for col in columnas_df:
                if re.search(patron, str(col), re.IGNORECASE):
                    mapeo[campo] = col
                    break
            if campo in mapeo:
                break

    return mapeo


# ============================================================
# 4. EXTRAER ÚLTIMO VALOR VÁLIDO DE CADA COLUMNA
# ============================================================
def extraer_ultimos_valores(df, mapping):
    resultado = {}

    for campo, col in mapping.items():
        if col not in df.columns:
            continue

        ultimo_valor = None
        for x in reversed(df[col].tolist()):
            val = limpiar_valor(x)
            if val is not None:
                ultimo_valor = val
                break

        resultado[campo] = ultimo_valor

    return resultado


def mapear_columnas_excel_a_modelo(nombre_hoja, columnas_df):
    """
    Wrapper para compatibilidad con admin.py
    """
    return mapear_columnas_por_hoja(nombre_hoja, columnas_df)


# ============================================================
# 5. EXTRAER DATOS DE POROSIDAD + PROMEDIO BJH
# ============================================================
def extraer_datos_porosidad(ruta_excel):
    hojas = ["BJHA", "BJHD", "HK", "DFT", "NKA", "FHHA"]

    valores = {}
    bjha = None
    bjhd = None

    try:
        xls = pd.ExcelFile(ruta_excel)

        for hoja in hojas:
            if hoja not in xls.sheet_names:
                continue

            df = pd.read_excel(xls, sheet_name=hoja)
            if df.empty:
                continue

            mapping = mapear_columnas_por_hoja(hoja, df.columns)
            if not mapping:
                continue

            extraidos = extraer_ultimos_valores(df, mapping)

            if hoja == "BJHA":
                bjha = extraidos.get("bjha_pore_volume")
            elif hoja == "BJHD":
                bjhd = extraidos.get("bjhd_pore_volume")
            else:
                valores.update(extraidos)

        # Promedio BJH
        valores_bjh = [v for v in (bjha, bjhd) if v is not None]
        valores["bjh_pore_volume_avg"] = (
            np.mean(valores_bjh) if valores_bjh else None
        )

    except Exception as e:
        print(f"ERROR en extraer_datos_porosidad: {e}")

    return valores


# ============================================================
# 6. EXTRAER RESULTADOS + VOLUMEN TOTAL DE POROSIDAD
# ============================================================
def extraer_resultado_calculos(ruta_excel):
    """
    Extrae:
    - Single BET
    - Desviación estándar
    - Volumen total de porosidad (micro + meso 1 + meso 2)
    """
    resultados = {
        "single_bet": None,
        "volumen_total_porosidad": None,
        "desviacion_estandar": None,
    }

    vol_micro = None
    vol_meso_1 = None
    vol_meso_2 = None

    try:
        df = pd.read_excel(
            ruta_excel,
            sheet_name="RESULTADO_CALCULOS",
            header=None
        )

        for _, fila in df.iterrows():
            etiqueta = str(fila[0]).lower()
            valor = limpiar_valor(fila[1])

            if valor is None:
                continue

            if "single" in etiqueta and "bet" in etiqueta:
                resultados["single_bet"] = valor

            elif "desviación" in etiqueta or "std" in etiqueta:
                resultados["desviacion_estandar"] = valor

            elif "microporos" in etiqueta:
                vol_micro = valor

            elif "7.7" in etiqueta or "180" in etiqueta:
                vol_meso_1 = valor

            elif "15" in etiqueta or "1767" in etiqueta:
                vol_meso_2 = valor

        volumenes = [v for v in (vol_micro, vol_meso_1, vol_meso_2) if v is not None]
        resultados["volumen_total_porosidad"] = sum(volumenes) if volumenes else None

    except Exception as e:
        print(f"ERROR en extraer_resultado_calculos: {e}")

    return resultados