import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

# =====================
# 1. Cargar datos BET
# =====================
df = pd.read_csv("BET_data.csv")

# Separo etiquetas (Sample) y características numéricas
samples = df["Sample"]
X = df.drop(columns=["Sample"]).values

# =====================
# 2. Escalado
# =====================
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# =====================
# 3. PCA
# =====================
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)

# =====================
# 4. t-SNE
# =====================
tsne = TSNE(n_components=2, random_state=42, perplexity=5, max_iter=2000, learning_rate="auto")
X_tsne = tsne.fit_transform(X_scaled)

# =====================
# 5. (Opcional) TCA si tienes 2 dominios distintos
# =====================
try:
    from tca import TCA
    # Ejemplo: primera mitad "dominio fuente", segunda "dominio destino"
    mid = len(X_scaled)//2
    Xs, Xt = X_scaled[:mid], X_scaled[mid:]
    Ys, Yt = samples[:mid], samples[mid:]

    tca = TCA(kernel_type='linear', dim=2)
    Xs_new, Xt_new = tca.fit(Xs, Xt)
    X_tca = np.vstack((Xs_new, Xt_new))
    Y_tca = np.hstack((Ys, Yt))
except:
    X_tca, Y_tca = None, None
    print(" TCA no disponible (pip install transfer-learning)")

# =====================
# 6. Visualización
# =====================
fig, axs = plt.subplots(1, 3 if X_tca is not None else 2, figsize=(15, 5))

# PCA
axs[0].scatter(X_pca[:,0], X_pca[:,1])
for i, txt in enumerate(samples):
    axs[0].annotate(txt, (X_pca[i,0], X_pca[i,1]))
axs[0].set_title("PCA (BET samples)")

# t-SNE
axs[1].scatter(X_tsne[:,0], X_tsne[:,1])
for i, txt in enumerate(samples):
    axs[1].annotate(txt, (X_tsne[i,0], X_tsne[i,1]))
axs[1].set_title("t-SNE (BET samples)")

# TCA
if X_tca is not None:
    axs[2].scatter(X_tca[:,0], X_tca[:,1])
    for i, txt in enumerate(Y_tca):
        axs[2].annotate(txt, (X_tca[i,0], X_tca[i,1]))
    axs[2].set_title("TCA (BET samples)")

plt.show()