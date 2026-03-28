import pandas as pd
import numpy as np
from scipy.stats import linregress

df = pd.read_csv("nka.csv")

# eliminar ceros
df = df[(df.iloc[:,0] > 0) & (df.iloc[:,1] > 0)]

# TRAMO NK NOVAWIN PAH (definitivo)
df = df[(df.iloc[:,0] >= 12) & (df.iloc[:,0] <= 22)]

x = np.log(df.iloc[:,0])
y = np.log(df.iloc[:,1])

m, b, r, _, _ = linregress(x, y)
D_NK = 2 - m

print("Pendiente NK:", m)
print("Fractal NK:", D_NK)
print("R:", r)
