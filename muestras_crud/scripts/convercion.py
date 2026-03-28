import sys
import pandas as pd

if len(sys.argv) != 3:
    print("Uso: python convercion.py archivo.csv archivo.xlsx")
    sys.exit(1)

ruta_csv = sys.argv[1]
ruta_xlsx = sys.argv[2]

df = pd.read_csv(ruta_csv, sep=",")
df.to_excel(ruta_xlsx, index=False)

print(f"Convertido: {ruta_csv} → {ruta_xlsx}")