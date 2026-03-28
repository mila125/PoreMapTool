import pandas as pd

# =========================
# 1. Leer archivo Excel
# =========================
df_raw = pd.read_excel("RESULTADOS.xlsx")
df_raw["Pore Type"] = df_raw["Pore Type"].str.strip()

# =========================
# 2. Procesar valores
# =========================
areas = []
detected_count = 0

for _, row in df_raw.iterrows():
    val = row["Value"]

    if isinstance(val, str) and val.lower() == "nd":
        continue
    else:
        area = float(val)
        areas.append(area)
        detected_count += 1

# =========================
# 3. Totales
# =========================
total_area = sum(areas)

# =========================
# 4. Dataset FINAL (1 fila)
# =========================
df_final = pd.DataFrame([{
    "Total_Pore_Area": total_area,
    "Detected_Pore_Types": detected_count
}])

print(df_final)

# =========================
# 5. Guardar
# =========================
df_final.to_excel("dataset_poros_PCA.xlsx", index=False)