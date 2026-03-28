import pandas as pd
import os
import chardet
import re
import pandas as pd  # <--- Importar aquí, global

def detectar_codificacion(ruta_txt):
    with open(ruta_txt, "rb") as f:
        rawdata = f.read(10000)
    return chardet.detect(rawdata)['encoding'] or 'utf-8'

def clean_header(headers):
    """Limpia encabezados: quita espacios extra y columnas vacías."""
    headers = [re.sub(r"\s+", " ", h).strip() for h in headers]
    headers = [h if h != "" else f"Col_{i+1}" for i, h in enumerate(headers)]
    return headers

def combinar_filas_header(rows_norm):
    """
    Detecta si hay varias filas de encabezado.
    Si la segunda fila no contiene datos numéricos, se combina con la primera.
    """
    max_cols = len(rows_norm[0])
    if len(rows_norm) > 1:
        non_numeric = sum(
            not any(c.strip().replace(".", "", 1).isdigit() for c in [rows_norm[1][i]])
            for i in range(max_cols)
        )
        if non_numeric >= max_cols // 2:
            header = [f"{rows_norm[0][i]} {rows_norm[1][i]}".strip() for i in range(max_cols)]
            data = rows_norm[2:]
            return clean_header(header), data
    return clean_header(rows_norm[0]), rows_norm[1:]

def detectar_delimitador(linea):
    """Detecta delimitador probable en una fila de texto."""
    if "\t" in linea:
        return "\t"
    elif "," in linea:
        return ","
    elif ";" in linea:
        return ";"
    else:
        # si no hay delimitadores claros → usar 2+ espacios como separador
        return r"\s{2,}"

def txt_a_excel_multi(ruta_txt, ruta_excel=None, output_dir="output_png"):
    if not os.path.exists(ruta_txt):
        raise FileNotFoundError(f"No se encontró el archivo: {ruta_txt}")

    # === Leer archivo y detectar encoding ===
    encoding = detectar_codificacion(ruta_txt)
    with open(ruta_txt, "r", encoding=encoding, errors="replace") as f:
        lines = [ln.rstrip("\n") for ln in f]

    # Detectar delimitador
    first_non_empty = next((ln for ln in lines if ln.strip() != ""), "")
    delimiter = detectar_delimitador(first_non_empty)

    # === Separar bloques (dos líneas vacías consecutivas) ===
    bloques, bloque_actual, empty_count = [], [], 0
    for ln in lines:
        if ln.strip() == "":
            empty_count += 1
        else:
            if empty_count >= 2 and bloque_actual:
                bloques.append(bloque_actual)
                bloque_actual = []
            empty_count = 0
            bloque_actual.append(ln)
    if bloque_actual:
        bloques.append(bloque_actual)

    # === Convertir cada bloque a DataFrame ===
    dataframes = []
    for bloque in bloques:
        bloque = [b for b in bloque if b.strip()]
        if not bloque:
            continue

        # Separar columnas por el delimitador
        if delimiter.startswith(r"\s"):
            rows = [re.split(delimiter, fila.strip()) for fila in bloque]
        else:
            rows = [fila.split(delimiter) for fila in bloque]

        max_cols = max(len(r) for r in rows)
        rows_norm = [r + [""] * (max_cols - len(r)) for r in rows]

        header, data = combinar_filas_header(rows_norm)
        df = pd.DataFrame(data, columns=header)
        dataframes.append(df)

    # === Nombres de hojas: primera INFORME vacía ===
    nombres = [

        "BET",
        "BJHA",
        "BJHD",
        "HK",
        "DFT",
        "NKA",
        "FHHA",
        "NKD",
        "FHHD"
        
    ]

    if ruta_excel is None:
        ruta_excel = os.path.splitext(ruta_txt)[0] + ".xlsx"

    # === Guardar todas las hojas ===
    with pd.ExcelWriter(ruta_excel, engine="openpyxl") as writer:
        # Hoja vacía “INFORME”
        pd.DataFrame({"": []}).to_excel(writer, sheet_name="INFORME", index=False)

        # Hojas con datos reales
        for idx, df in enumerate(dataframes):
            nombre = nombres[idx + 1] if idx + 1 < len(nombres) else f"Hoja_{idx+2}"
            df.to_excel(writer, sheet_name=nombre[:31], index=False)

    print(f" Archivo convertido a Excel con {len(dataframes) + 1} hojas: {ruta_excel}")
    return ruta_excel