import pandas as pd

def bjh_average(csv_file):
    df = pd.read_csv(csv_file)

    radius = df["Radius"]      # Å
    dVlogr = df["dV(logr)"]

    # Filtro físico
    mask = (radius < 200) & (dVlogr > 0)
    radius = radius[mask]
    dVlogr = dVlogr[mask]

    # Promedio ponderado (radio)
    radius_avg = (radius * dVlogr).sum() / dVlogr.sum()

    # Convertir a DIÁMETRO
    diameter_A = 2 * radius_avg
    diameter_nm = diameter_A / 10

    return diameter_A, diameter_nm


# Calcular adsorción y desorción
ads_A, ads_nm = bjh_average("BJHA.csv")
des_A, des_nm = bjh_average("BJHD.csv")

# Promedio entre ambos
avg_A = (ads_A + des_A) / 2
avg_nm = (ads_nm + des_nm) / 2

# Imprimir resultados
print("Adsorption BJH Volume Average Diameter:")
print(f"  {ads_A:.3f} Å")
print(f"  {ads_nm:.3f} nm\n")

print("Desorption BJH Volume Average Diameter:")
print(f"  {des_A:.3f} Å")
print(f"  {des_nm:.3f} nm\n")

print("Average BJH Volume Average Diameter (Ads + Des) / 2:")
print(f"  {avg_A:.3f} Å")
print(f"  {avg_nm:.3f} nm")