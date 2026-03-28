import sys
import pandas as pd
import os
from matplotlib.backends.backend_pdf import PdfPages
from visualizaciones import (
    draw_comparison_bar_chart,
    draw_HK,
    draw_DFT
)

# IMPORTACIÓN DE TUS MÓDULOS DE ANÁLISIS
from tests_bet import tests_main
from modelo_geometrico import gmain
from modelo_fractal import fmain
def leer_csv_hk(archivo):
    try:
        df = pd.read_csv(archivo, sep=None, engine="python", header=None)
        df = df.apply(pd.to_numeric, errors="coerce")
        df = df.dropna()

        if df.shape[1] < 2:
            raise ValueError("HK requiere al menos 2 columnas")

        return df.iloc[:, [0, 1]]  # x = half pore width, y = dV
    except Exception as e:
        print(f"[HK] Error leyendo {archivo}: {e}")
        return pd.DataFrame()
def convertir_csv_a_xlsx_bet(ruta_csv):
    """
    Convierte el archivo CSV de datos BET a Excel con la hoja requerida 'BET'.
    """
    try:
        print(f"Convertiendo {ruta_csv} a formato Excel...")
        # Leer CSV (detectando separador automáticamente)
        df = pd.read_csv(ruta_csv, sep=None, engine='python')
        
        # Crear nombre para el nuevo archivo excel
        ruta_xlsx = ruta_csv.lower().replace('.csv', '.xlsx')
        
        # Guardar con el nombre de hoja 'BET' que esperan los otros scripts
        with pd.ExcelWriter(ruta_xlsx, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='BET', index=False)
        
        print(f" Conversión exitosa: {ruta_xlsx}")
        return ruta_xlsx
    except Exception as e:
        print(f" Error convirtiendo CSV a Excel: {e}")
        return None

def leer_csv_directo(archivo):
    """Lee el CSV y extrae las columnas de Radio (0) y dV (3) limpiando texto."""
    try:
        df = pd.read_csv(archivo, sep=None, engine='python', header=None, on_bad_lines='skip')
        df_numeric = df.apply(pd.to_numeric, errors="coerce")
        df_limpio = df_numeric.dropna(subset=[0, 3])
        return df_limpio.iloc[:, [0, 3]] 
    except Exception as e:
        print(f"Error leyendo {archivo}: {e}")
        return pd.DataFrame()

def main():
    if len(sys.argv) < 4:
        print("Uso: python testvisa.py bjha.csv bjhd.csv bet_data.csv (o .xlsx)")
        return

    archivo_ads = sys.argv[1]
    archivo_des = sys.argv[2]
    archivo_hk  = sys.argv[3]   # HK
    ruta_entrada_bet = sys.argv[4] # Puede ser .csv o .xlsx

    output_dir = os.path.join(os.getcwd(), "output_png")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # --- PASO PREVIO: VALIDACIÓN Y CONVERSIÓN ---
    if ruta_entrada_bet.lower().endswith('.csv'):
        ruta_excel = convertir_csv_a_xlsx_bet(ruta_entrada_bet)
        if not ruta_excel: return # Detener si falla la conversión
    else:
        ruta_excel = ruta_entrada_bet

    try:
        # --- 1. PROCESAMIENTO BJH ---
        print("\n--- Procesando BJH Ads / Des ---")
        df_ads = leer_csv_directo(archivo_ads)
        df_des = leer_csv_directo(archivo_des)

        if not df_ads.empty and not df_des.empty:
         draw_comparison_bar_chart(df_ads, df_des, output_dir=output_dir)

        #2 --- HK ---
        print("\n--- Ejecutando HK ---")
        df_hk = leer_csv_hk(archivo_hk)

        if not df_hk.empty:
          draw_HK(df_hk)
        else:
          print("[HK] Archivo HK vacío o inválido")

        # --- 3. DFT ---
        print("\n--- Ejecutando DFT ---")
        draw_DFT(df_ads)
        
        # --- 2. EJECUCIÓN TESTS BET ---
        print(f"\n--- Ejecutando Tests BET ---")
        # Esto genera la hoja 'RESULTADOS_BET' dentro del excel (o un excel nuevo de resultados)
        ruta_resultados_bet = tests_main(ruta_excel, output_dir=output_dir)
        
        # --- 3. GENERACIÓN DE MODELOS Y REPORTE PDF ---
        nombre_base = os.path.splitext(os.path.basename(ruta_excel))[0]
        ruta_pdf = os.path.join(output_dir, f"Reporte_Modelos_{nombre_base}.pdf")
        
        print(f"\n--- Generando Modelos Fractal y Geométrico en PDF ---")
        with PdfPages(ruta_pdf) as pdf:
            # Modelo Fractal
            try:
                fig_f = fmain("RESULTADOS.XLSX")
                if fig_f:
                    pdf.savefig(fig_f)
                    print(" Modelo Fractal añadido al PDF.")
            except Exception as e:
                print(f" Error en Modelo Fractal: {e}")

            # Modelo Geométrico
            try:
                fig_g = gmain("RESULTADOS.XLSX") 
                if fig_g:
                    pdf.savefig(fig_g)
                    print(" Modelo Geométrico añadido al PDF.")
            except Exception as e:
                print(f" Error en Modelo Geométrico: {e}")

        print(f"\n Proceso finalizado con éxito.")
        print(f" Resultados en: {output_dir}")

    except Exception as e:
        print(f" Error crítico en el proceso: {e}")

if __name__ == "__main__":
    main()