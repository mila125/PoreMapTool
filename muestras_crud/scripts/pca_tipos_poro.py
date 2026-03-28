import os
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

# Carpeta donde están tus Excel generados (_hash_resultados.xlsx)
CARPETA_EXCEL = r"C:\QCdata\Reports"

# Leer todos los Excel y combinarlos
datos = []

for archivo in os.listdir(CARPETA_EXCEL):
    if archivo.endswith("_hash_resultados.xlsx"):
        ruta = os.path.join(CARPETA_EXCEL, archivo)
        xls = pd.ExcelFile(ruta)
        muestra_dict = {}

        # Tomar hojas relevantes (ejemplo: DFT, BJHA, BJHD, BET, HK)
        for hoja in ["DFT", "BJHA", "BJHD", "BET", "HK"]:
            if hoja in xls.sheet_names:
                df = pd.read_excel(ruta, sheet_name=hoja)
                # Promediar columnas numéricas
                for col in df.select_dtypes(include="number").columns:
                    muestra_dict[f"{hoja}_{col}"] = df[col].mean()

        # Guardar nombre de la muestra
        muestra_dict["sample_number"] = archivo.replace("_hash_resultados.xlsx", "")
        datos.append(muestra_dict)

df_final = pd.DataFrame(datos).fillna(0)
sample_names = df_final.pop("sample_number")  # Guardar para etiquetas

# Estandarizar los datos
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df_final)

# Aplicar PCA
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)

# Clustering (KMeans) para denotar tipos de poros
kmeans = KMeans(n_clusters=3, random_state=42)
tipos = kmeans.fit_predict(X_pca)

# Guardar resultados
df_resultados = pd.DataFrame({
    "sample_number": sample_names,
    "PCA1": X_pca[:,0],
    "PCA2": X_pca[:,1],
    "tipo_poro": tipos
})

df_resultados.to_csv(os.path.join(CARPETA_EXCEL, "tipos_poros.csv"), index=False)
print("Resultados PCA guardados en tipos_poros.csv")

# Visualización
plt.figure(figsize=(8,6))
for t in df_resultados["tipo_poro"].unique():
    subset = df_resultados[df_resultados["tipo_poro"] == t]
    plt.scatter(subset["PCA1"], subset["PCA2"], label=f"Tipo {t}", s=100)
plt.xlabel("PCA1")
plt.ylabel("PCA2")
plt.title("Tipos de poros según PCA")
plt.legend()
plt.show()
