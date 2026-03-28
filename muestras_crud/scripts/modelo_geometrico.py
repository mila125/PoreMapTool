import sys
import os

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import rotate

def generar_modelo_pcc(datos, nombre_muestra, escala_nm=20, output_dir="output_geom"):
    os.makedirs(output_dir, exist_ok=True)
    ancho, alto = 500, 500
    lienzo = np.zeros((alto, ancho))
    centro_x = ancho // 2
    
    # Escalado de datos
    f_escala = 5000
    w_placa = int(datos["Placa"] * f_escala)
    w_nodif = int(datos["Nodiferenciados"] * f_escala)
    w_micro = int(datos["Microporos"] * f_escala)
    
    # Parámetros del tronco
    y_suelo = alto - 50
    h_tronco = 300
    y_tope = y_suelo - h_tronco
    
    # --- LÓGICA DE RAMIFICACIÓN CONDICIONAL ---
    # Verificamos si el ancho de la placa o el cuerpo exceden el margen del cuadro
    # o si la altura total se sale del lienzo.
    excede_ancho = (centro_x + w_placa // 2) >= ancho or (centro_x - w_placa // 2) <= 0
    excede_alto = y_tope <= 20
    
    cab_en_cuadro = not (excede_ancho or excede_alto)

    # 2. DIBUJAR ESTRUCTURA BASE
    # Dibujamos el tronco (siempre está presente, pero su forma cambia)
    lienzo[y_suelo-60:y_suelo, centro_x - w_placa//2 : centro_x + w_placa//2] = 1
    lienzo[y_tope:y_suelo, centro_x - w_nodif*2 : centro_x + w_nodif*2] = 1

    # 3. RAMIFICACIÓN (Solo si NO cabe en el cuadro)
    if not cab_en_cuadro:
        def añadir_rama(x_org, y_org, angulo, largo, grosor):
            rama = np.ones((largo, grosor))
            for i in range(0, largo, 8):
                rama[i:i+2, :] = 1 
            rama_rotada = rotate(rama, angulo, reshape=True, order=0)
            h_r, w_r = rama_rotada.shape
            y_pos = y_org - h_r // 2
            x_pos = x_org - w_r // 2
            try:
                region = lienzo[y_pos:y_pos+h_r, x_pos:x_pos+w_r]
                lienzo[y_pos:y_pos+h_r, x_pos:x_pos+w_r] = np.maximum(region, rama_rotada)
            except: pass

        y_union = y_suelo - 100
        # Si no cabe, ramifica para distribuir el volumen
        añadir_rama(centro_x - 20, y_union, 45, 130, w_micro + 4)
        añadir_rama(centro_x + 20, y_union, -45, 130, w_micro + 4)
        print(f"  > [{nombre_muestra}]: Ramificación activada (Dimensiones excedidas).")
    else:
        print(f"  > [{nombre_muestra}]: Estructura lineal (Cabe perfectamente en el cuadro).")

    # 4. TEXTURA SERRADA
    for y in range(y_tope, y_suelo, 12):
        ancho_serrado = (w_nodif * 4) + 10
        lienzo[y:y+3, centro_x - ancho_serrado//2 : centro_x + ancho_serrado//2] = 1

    # 5. RENDERIZADO
    fig, ax = plt.subplots(figsize=(7, 7), facecolor='#999999')
    ax.imshow(lienzo, cmap='gray_r', origin='upper')
    ax.plot([ancho-120, ancho-40], [40, 40], color='black', lw=6)
    ax.text(ancho-115, 75, f"{escala_nm} nm", color='black', fontsize=10, weight='bold')
    ax.axis('off')
    ax.set_title(f"Modelo: {nombre_muestra}")

    output_path = os.path.join(output_dir, f"{nombre_muestra}_geom.png")
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    
    return fig
# 1. FUNCIÓN PARA CARGAR LOS DATOS
def cargar_datos_excel(ruta_archivo):
    # Leemos el excel. Suponemos que la primera columna ('MUESTRA') es el índice
    df = pd.read_excel(ruta_archivo, index_col=0)
    
    # Reemplazamos 'nd' por 0 para poder operar matemáticamente
    df = df.replace('nd', 0).fillna(0)
    
    # Convertimos a flotantes por si acaso
    return df.astype(float)

# 2. FUNCIÓN GENERADORA (Versión Universal Mejorada)
def generar_modelo_desde_df(nombre_muestra, serie_datos):
    # Mapeo de nombres del Excel a variables del código
    datos = {
        "Placa": serie_datos.get("Plate", 0),
        "Nodiferenciados": serie_datos.get("Unclassified", 0),
        "Microporos": serie_datos.get("Micro", 0)
    }
    
    # Determinamos el tipo de modelo por el nombre de la columna
    tipo = "PCC" if "PCC" in nombre_muestra else "PAH"
    
    # Aquí llamaríamos a la lógica de dibujo (reutilizando la del paso anterior)
    print(f"Generando modelo para {nombre_muestra} ({tipo})...")
    # (El resto del código de dibujo va aquí...)
    generar_modelo_pcc(datos, nombre_muestra,escala_nm=20)
def leer_resultados_bet(ruta_excel):
    """
    Lee la hoja RESULTADOS_BET con formato:
    Pore Type | Value
    """

    df = pd.read_excel(
        ruta_excel,
        sheet_name="RESULTADOS_BET",
        dtype=str
    )

    df.columns = [c.strip() for c in df.columns]

    df["Pore Type"] = df["Pore Type"].str.strip()
    df["Value"] = df["Value"].str.strip()

    # coma decimal → punto
    df["Value"] = df["Value"].str.replace(",", ".", regex=False)
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce").fillna(0)

    # convertir a diccionario compatible con el modelo
    # convertir a diccionario compatible con el modelo
    datos = {
        "Placa": df.loc[df["Pore Type"] == "Plate", "Value"].sum(),
        "Nodiferenciados": df.loc[df["Pore Type"] == "Unclassified", "Value"].sum(),
        "Microporos": df.loc[df["Pore Type"] == "Micro", "Value"].sum(),
    }

    return datos
def gmain(ruta_excel):


    print(" Iniciando gmain()")

    if not os.path.exists(ruta_excel):
        print(f" El archivo no existe: {ruta_excel}")
        return False

    try:
        datos = leer_resultados_bet(ruta_excel)

        print(" Datos BET leídos correctamente:")
        print(datos)

        nombre_muestra = os.path.splitext(os.path.basename(ruta_excel))[0]
          
    
        fig = generar_modelo_pcc(datos, nombre_muestra)
        return generar_modelo_pcc(datos, nombre_muestra)

    except Exception as e:
        print(f" Error en gmain: {e}")
        return False
    
# --- PROCESO PRINCIPAL ---
if __name__ == "__main__":

    if len(sys.argv) < 2:
        print(" Uso incorrecto")
        print(" Uso correcto: python modelos.py archivo.xlsx")
        sys.exit(1)

    ruta = sys.argv[1]

    ok = gmain(ruta)

    if not ok:
        sys.exit(1)