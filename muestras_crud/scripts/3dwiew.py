import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from sklearn.preprocessing import MinMaxScaler
import matplotlib.patches as mpatches # Importar para crear proxy handles

# --- [Parte de Carga y Limpieza de Datos - SIN CAMBIOS] ---
ruta_excel = r"C:\Users\6lady\OneDrive\Escritorio\ramos_usm\herramientas\crud\muestras\muestras\media\informes\xlsx\DK01A_report_01.xlsx"
df_bet = pd.read_excel(ruta_excel, sheet_name="BET")
df_bjha = pd.read_excel(ruta_excel, sheet_name="BJHA")
df_bjhd = pd.read_excel(ruta_excel, sheet_name="BJHD")
df_dft = pd.read_excel(ruta_excel, sheet_name="DFT")

def limpiar_dataframe(df):
    df = df.iloc[1:].reset_index(drop=True) 
    df = df.apply(pd.to_numeric, errors="coerce")
    df = df.dropna()
    return df

df_bjh_promedio = df_bjha.copy()
df_bjh_promedio[df_bjha.select_dtypes(include="number").columns] = (df_bjha[df_bjha.select_dtypes(include="number").columns] + df_bjhd[df_bjhd.select_dtypes(include="number").columns]) / 2
df_bjh_promedio = limpiar_dataframe(df_bjh_promedio)

df_bet = limpiar_dataframe(df_bet)
df_dft = limpiar_dataframe(df_dft)

df_bet = df_bet.sort_values(df_bet.columns[0])
df_bjh_promedio = df_bjh_promedio.sort_values("Radius Area")
df_dft = df_dft.sort_values(df_dft.columns[0])

scaler = MinMaxScaler()
df_bet_scaled = scaler.fit_transform(df_bet)
df_bjh_promedio_scaled = scaler.fit_transform(df_bjh_promedio[["Radius Area", "Pore Volume"]])
df_dft_scaled = scaler.fit_transform(df_dft)

# ------------------------------------------------
# Funciones de visualización - SIN CAMBIOS
# ------------------------------------------------

def plot_3d_wave_surface(x, z_base, y_level, ax, color_map="viridis", amplitude=0.1, frequency=2, width=0.2):
    """
    Esta función dibuja una superficie en 3D con forma de onda.
    """
    y_band = np.linspace(y_level - width/2, y_level + width/2, 20)
    X, Y = np.meshgrid(x, y_band)
    
    Z_base_matrix = np.tile(z_base, (len(y_band), 1))
    
    wave = np.sin(frequency * X) * amplitude 
    
    Z_wave = Z_base_matrix + wave
    
    ax.plot_surface(X, Y, Z_wave, cmap=color_map, edgecolor="none", alpha=0.8, antialiased=False)


# ------------------------------------------------
# Crear gráfico 3D - CON LEYENDA EN 'upper left'
# ------------------------------------------------
fig = plt.figure(figsize=(12,8))
ax = fig.add_subplot(111, projection="3d")

# Definir los colores base (usados para los 'proxy handles' de la leyenda)
color_bet = 'darkblue'
color_bjh = 'darkgreen'
color_dft = 'darkred'

# 1. Dibujar las superficies onduladas
plot_3d_wave_surface(
    df_bet_scaled[:, 0], 
    df_bet_scaled[:, 1], 
    0, 
    ax, 
    color_map="Blues", 
    amplitude=0.1, 
    frequency=1.5,
    width=0.2
)

plot_3d_wave_surface(
    df_bjh_promedio_scaled[:, 0], 
    df_bjh_promedio_scaled[:, 1], 
    1, 
    ax, 
    color_map="Greens", 
    amplitude=0.1, 
    frequency=2.5,
    width=0.2
)

plot_3d_wave_surface(
    df_dft_scaled[:, 0], 
    df_dft_scaled[:, 1], 
    2, 
    ax, 
    color_map="Reds", 
    amplitude=0.1, 
    frequency=3.0,
    width=0.2
)

# 2. Configuración de los ejes
ax.set_yticks([0, 1, 2])
ax.set_yticklabels(["BET", "BJH", "DFT"])

ax.set_xlabel("Variable estructural (Normalizada)")
ax.set_zlabel("Volumen (Normalizado)")
ax.set_title("Comparación 3D de Superficies Onduladas de Isoterma")

ax.set_zlim(np.min(df_bet_scaled[:, 1]) - 0.2, np.max(df_dft_scaled[:, 1]) + 0.2)
ax.view_init(elev=20, azim=-60)

# 3. Crear los elementos 'proxy' para la leyenda
bet_patch = mpatches.Patch(color=color_bet, label='BET', alpha=0.8)
bjh_patch = mpatches.Patch(color=color_bjh, label='BJH Promedio', alpha=0.8)
dft_patch = mpatches.Patch(color=color_dft, label='DFT', alpha=0.8)

# 4. Mostrar la leyenda usando los elementos proxy (ubicación modificada)
ax.legend(
    handles=[bet_patch, bjh_patch, dft_patch], 
    loc='upper left', 
    title='Método de Isoterma'
)

# Mostrar el gráfico
plt.show()