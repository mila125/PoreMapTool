import pandas as pd
import numpy as np
from scipy.stats import linregress

# =========================
# NK DATAFRAME
# =========================
df_nk = pd.DataFrame({
    "Radius": [
        2205,178.57,93.98,57.724,41.954,32.657,26.439,21.896,18.686,
        15.95,13.773,12.003,10.462,9.1372,7.9558,6.9334,5.9606,
        5.1213,4.2038,3.4051
    ],
    "Area": [
        0,0.51024,0.77283,1.0396,1.2512,1.4111,1.5954,1.7491,
        1.891,1.9905,2.1148,2.2564,2.4067,2.546,2.7331,2.9326,
        3.1524,3.3958,3.7623,4.2585
    ]
})

# Eliminar ceros (no físicos)
df_nk = df_nk[df_nk["Area"] > 0]

# Transformación log-log
x_nk = np.log(df_nk["Radius"])
y_nk = np.log(df_nk["Area"])

# Regresión
slope_nk, intercept, r_nk, p, se = linregress(x_nk, y_nk)

# Número fractal NK
D_NK = 2 - slope_nk

# =========================
# FHH DATAFRAME
# =========================
df_fhh = pd.DataFrame({
    "log_log_P": [
        -2.726,-1.6344,-1.3556,-1.1439,-1.0054,-0.89655,-0.80483,
        -0.72294,-0.65409,-0.58534,-0.52162,-0.46187,-0.40219,
        -0.34339,-0.28326,-0.22353,-0.15787,-0.091956,-0.0062247,
        0.085292
    ],
    "log_Vads": [
        0.9632,0.57264,0.43019,0.31722,0.24142,0.19136,0.13976,
        0.10057,0.067473,0.046392,0.022572,-0.0023424,-0.026733,
        -0.047509,-0.073176,-0.098457,-0.124,-0.1498,-0.18472,
        -0.22679
    ]
})

# Regresión FHH
x_fhh = df_fhh["log_log_P"]
y_fhh = df_fhh["log_Vads"]

slope_fhh, intercept, r_fhh, p, se = linregress(x_fhh, y_fhh)

# Número fractal FHH
D_FHH = 3 + slope_fhh

# =========================
# RESULTADOS
# =========================
print("===== RESULTADOS FRACTALES =====")
print(f"Numero de fractal (NK):  {D_NK:.3f}")
print(f"R² NK:                  {r_nk**2:.3f}\n")

print(f"Numero de fractal (FHH): {D_FHH:.3f}")
print(f"R² FHH:                 {r_fhh**2:.3f}")