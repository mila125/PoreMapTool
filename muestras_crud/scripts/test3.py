import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, PathPatch
from matplotlib.path import Path
import numpy as np

# Lista para guardar todos los óvalos y ríos
patches = []

def dibujar_fractal_rio(ax, x, y, ancho, alto, nivel, max_nivel):
    if nivel > max_nivel:
        return
    
    # Dibujar el óvalo actual sin borde visible
    oval = Ellipse((x, y), width=ancho, height=alto, facecolor='orange', alpha=0.6, edgecolor=None)
    ax.add_patch(oval)
    patches.append(oval)
    
    # Tamaño de sub-óvalos
    nuevos_anchos = [ancho * 0.6, ancho * 0.5, ancho * 0.4]
    nuevos_altos = [alto * 0.6, alto * 0.5, alto * 0.4]
    
    for i in range(len(nuevos_anchos)):
        dx = np.random.uniform(-0.2, 0.2) + (i - 1) * 0.5
        dy = alto * 0.7
        nuevo_x = x + dx
        nuevo_y = y + dy
        
        # Crear transición tipo "río" solo con relleno, sin borde
        verts = [
            (x - ancho/2, y),
            (x + dx/2, y + dy/2 + np.random.uniform(-0.1, 0.1)),
            (nuevo_x - nuevos_anchos[i]/2, nuevo_y),
            (nuevo_x + nuevos_anchos[i]/2, nuevo_y),
            (x + dx/2, y + dy/2 - np.random.uniform(-0.1, 0.1)),
            (x + ancho/2, y),
            (x - ancho/2, y)
        ]
        codes = [
            Path.MOVETO,
            Path.CURVE3,
            Path.CURVE3,
            Path.LINETO,
            Path.CURVE3,
            Path.CURVE3,
            Path.CLOSEPOLY
        ]
        path = Path(verts, codes)
        patch = PathPatch(path, facecolor='orange', alpha=0.4, edgecolor=None)
        ax.add_patch(patch)
        patches.append(patch)
        
        # Llamada recursiva
        dibujar_fractal_rio(ax, nuevo_x, nuevo_y, nuevos_anchos[i], nuevos_altos[i], nivel + 1, max_nivel)

# Configuración de la figura
fig, ax = plt.subplots(figsize=(6, 8))
ax.set_xlim(0, 10)
ax.set_ylim(0, 15)

# Dibujar fractal tipo río
dibujar_fractal_rio(ax, x=5, y=1, ancho=2, alto=1.5, nivel=1, max_nivel=4)

# Aplicar contorno general (opcional)
for p in patches:
    p.set_edgecolor('brown')  # borde visible
    p.set_facecolor(p.get_facecolor())  # conservar relleno
    p.set_linewidth(1)

ax.set_aspect('equal')
ax.axis('off')
plt.show()