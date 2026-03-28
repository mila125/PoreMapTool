import sys
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import pandas as pd
import os
import numpy as np
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import alphashape
from shapely.geometry import Polygon, MultiPolygon

# ============================================================
# ---------------------- CONFIGURACIÓN GLOBAL ------------------------
# ============================================================
MAX_LEVEL_PORE_TYPES = 5
BRANCHING_FACTOR = 3 
THICKNESS_FACTOR = 0.35
LENGTH_FACTOR = 0.35
COLLISION_STEP = 0.1
COLLISION_MAX_ATTEMPTS = 5
ALL_RECTS = []
TOLERANCE = 1.5

# Rangos de tamaño para la leyenda/piechart
RANGOS_NM = {
    "Plate": "3.6-36 nm",
    "Unclassified": "2-3.6 nm",
    "Micropores": "1.5-2 nm"
}
# ============================================================
# ---------------------- FUNCIONES AUXILIARES ------------------------
# ============================================================
def rects_to_field(rects, resolution=2000):
    """
    Convierte la lista de rectángulos en un campo 2D.
    """
    all_x = [r[0] for r in rects] + [r[1] for r in rects]
    all_y = [r[2] for r in rects] + [r[3] for r in rects]

    x_min, x_max = min(all_x), max(all_x)
    y_min, y_max = min(all_y), max(all_y)

    field = np.zeros((resolution, resolution))

    def x_to_i(x):
        return int((x - x_min) / (x_max - x_min) * (resolution - 1))

    def y_to_j(y):
        return int((y - y_min) / (y_max - y_min) * (resolution - 1))
    field += 0.15 * np.random.random(field.shape)

    for min_x, max_x, min_y, max_y in rects:
        i1, i2 = x_to_i(min_x), x_to_i(max_x)
        j1, j2 = y_to_j(min_y), y_to_j(max_y)
        field[j1:j2, i1:i2] += 0.6


    extent = [x_min, x_max, y_min, y_max]
    return field, extent


def compute_total_branches_per_level(max_level, branching_factor):
      """Calcula el número total de ramas por nivel, aunque no se usa directamente en el dibujo."""
      branches = {}
      branches[0] = 1
      for i in range(1, max_level):
            branches[i] = branches[i-1] * branching_factor
      return branches

def compute_branch_dims(w_base, h_base, k):
    return w_base * THICKNESS_FACTOR, h_base * LENGTH_FACTOR

# ============================================================
# ---------------------- DIBUJO BÁSICO Y COLISIÓN ------------------------
# ============================================================

def draw_rect(ax, x, y, w, h, name, color):
    if w < 0: x += w; w = abs(w)
    if h < 0: y += h; h = abs(h)
    rect = Rectangle((x - w / 2, y), w, h, facecolor=color, alpha=0.9, edgecolor="black", linewidth=1, zorder=10)
    ax.add_patch(rect)
    return x - w / 2, x + w / 2, y, y + h

def check_collision_and_register(positions_matrix, rect_bounds, name):
    global ALL_RECTS
    min_x_new, max_x_new, min_y_new, max_y_new = rect_bounds
    for existing_name, (min_x_old, max_x_old, min_y_old, max_y_old) in positions_matrix.items():
        if (max_x_new > min_x_old + TOLERANCE and min_x_new < max_x_old - TOLERANCE and
            max_y_new > min_y_old + TOLERANCE and min_y_new < max_y_old - TOLERANCE):
            return False
    positions_matrix[name] = rect_bounds
    ALL_RECTS.append(rect_bounds)
    return True

# ============================================================
# ---------------------- DIBUJO VERTICAL ----------------------
# ============================================================
def draw_vertical_branch(ax, parent_info, all_pore_data, current_index,
                         positions_matrix, direction_v=1):

    if current_index >= len(all_pore_data):
        return

    pore = all_pore_data[current_index]
    name, w_base, h_base, color = (
        pore['name'], pore['w'], pore['h'], pore['color']
    )

    # ---------------------------------
    # DATOS DEL PADRE
    # ---------------------------------
    px_parent, py_anchor, _, _ = parent_info

    # ---------------------------------
    # DIMENSIONES
    # ---------------------------------
    draw_w, draw_h = compute_branch_dims(
        w_base, h_base, BRANCHING_FACTOR
    )
    half_w = draw_w / 2

    # ---------------------------------
    # POSICIÓN Y (anclaje real)
    # ---------------------------------
    if direction_v == 1:
        start_y = py_anchor
    else:
        start_y = py_anchor - draw_h

    # ---------------------------------
    # BÚSQUEDA X SEGURA (CON COLOR)
    # ---------------------------------
    offsets = [0.0]
    for i in range(1, COLLISION_MAX_ATTEMPTS + 1):
        step = i * draw_w * COLLISION_STEP
        offsets.extend([step, -step])

    center_x = px_parent
    found = False

    for dx in offsets:
        cx = px_parent + dx

        min_x = cx - half_w
        max_x = cx + half_w
        min_y = start_y
        max_y = start_y + draw_h

        blocked = False

        for key, (ox1, ox2, oy1, oy2) in positions_matrix.items():

            overlap = (
                max_x > ox1 + TOLERANCE and
                min_x < ox2 - TOLERANCE and
                max_y > oy1 + TOLERANCE and
                min_y < oy2 - TOLERANCE
            )

            if not overlap:
                # print("no solapa!")
                continue

            # ---------------------------------
            # MISMO COLOR → mover X
            # ---------------------------------
            # Nota: La key de positions_matrix ahora incluye el color, 
            # permitiendo distinguir el solape por tipo de poro.
            if key.endswith(f"_{color}"):
                # print("mismo color!")
                blocked = True
                break

            # ---------------------------------
            # COLOR DISTINTO → prohibido
            # ---------------------------------
            # print("distinto!")
            blocked = True
            break

        if not blocked:
            center_x = cx
            found = True
            break

    # fallback limpio
    if not found:
        center_x = px_parent

    # ---------------------------------
    # DIBUJO VERTICAL
    # ---------------------------------
    rect_bounds = draw_rect(
        ax,
        center_x,
        start_y,
        draw_w,
        draw_h,
        f"{name}_V_{current_index}",
        color
    )

    # La clave en positions_matrix incluye el color para la comprobación de colisiones
    check_collision_and_register(
        positions_matrix,
        rect_bounds,
        f"{name}_V_{center_x:.2f}_{start_y:.2f}_{current_index}_{color}"
    )

    # ---------------------------------
    # HOJA
    # ---------------------------------
    if current_index == len(all_pore_data) - 1:
        return

    # ---------------------------------
    # SIGUIENTE NIVEL
    # ---------------------------------
    next_index = current_index + 1
    next_pore = all_pore_data[next_index]

    _, next_thickness = compute_branch_dims(
        next_pore['w'], next_pore['h'], BRANCHING_FACTOR
    )

    # anclaje real del siguiente
    if direction_v == 1:
        next_anchor_y = start_y + draw_h
    else:
        next_anchor_y = start_y

    # ---------------------------------
    # CONTINUACIÓN VERTICAL
    # ---------------------------------
    draw_vertical_branch(
        ax,
        (center_x, next_anchor_y, draw_h, next_thickness),
        all_pore_data,
        next_index,
        positions_matrix,
        direction_v=direction_v
    )

    # ---------------------------------
    # RAMAS HORIZONTALES (SIN CAMBIOS)
    # ---------------------------------
    mid_y = start_y + draw_h / 2
    start_y_h = mid_y - next_thickness / 2

    draw_horizontal_branch(
        ax,
        (center_x - half_w, start_y_h, 0, next_thickness),
        all_pore_data,
        next_index,
        positions_matrix,
        direction='left'
    )

    draw_horizontal_branch(
        ax,
        (center_x + half_w, start_y_h, 0, next_thickness),
        all_pore_data,
        next_index,
        positions_matrix,
        direction='right'
    )

# ============================================================
# --------------------- DIBUJO HORIZONTAL --------------------
# ============================================================
def draw_horizontal_branch(ax, parent_info, all_pore_data, current_index,
                           positions_matrix, direction='left'):
    """
    Dibuja un segmento de rama horizontal, maneja colisiones en Y,
    y luego invoca las ramas verticales.
    """

    if current_index >= len(all_pore_data):
        return

    pore = all_pore_data[current_index]
    name, w_base, h_base, color = (
        pore['name'], pore['w'], pore['h'], pore['color']
    )

    # ---------------------------
    # DATOS DEL PADRE (solo posición)
    # ---------------------------
    px_parent_end, start_y, _, _ = parent_info

    # ---------------------------
    # DIMENSIONES HORIZONTALES
    # ---------------------------
    draw_w, draw_h = compute_branch_dims(
        w_base, h_base, BRANCHING_FACTOR
    )

    # ---------------------------
    # POSICIÓN HORIZONTAL
    # ---------------------------
    if direction == 'left':
        center_x = px_parent_end - draw_w / 2
        next_x = px_parent_end - draw_w
    else:
        center_x = px_parent_end + draw_w / 2
        next_x = px_parent_end + draw_w

    # ---------------------------
    # AJUSTE DE Y (EVITAR SOLAPE)
    # ---------------------------
    y_offset = 0.0
    initial_y = start_y
    # Se añade un margen extra en los intentos para el caso horizontal
    for _ in range(COLLISION_MAX_ATTEMPTS * 2):
        y_test = initial_y - y_offset

        min_x = center_x - draw_w / 2
        max_x = center_x + draw_w / 2
        min_y = y_test
        max_y = y_test + draw_h

        safe = True
        for (_, (ox1, ox2, oy1, oy2)) in positions_matrix.items():
            if (
                max_x > ox1 + TOLERANCE and min_x < ox2 - TOLERANCE and
                max_y > oy1 + TOLERANCE and min_y < oy2 - TOLERANCE
            ):
                safe = False
                break

        if safe:
            start_y = y_test
            # print(f"  [INFO] H-Branch Y-Adjust: {initial_y:.2f} -> {start_y:.2f} (Offset: {y_offset:.2f})")
            break

        y_offset += draw_h * COLLISION_STEP
        if _ == COLLISION_MAX_ATTEMPTS * 2 - 1:
            # print(f"  [WARN] Horizontal Y-collision failed for {name}. Using original Y.")
            pass


    # ---------------------------
    # DIBUJO HORIZONTAL
    # ---------------------------
    rect_limits = draw_rect(
        ax, center_x, start_y, draw_w, draw_h,
        f"{name}_H_{current_index}", color
    )
    # La clave en positions_matrix incluye el color para la comprobación de colisiones
    check_collision_and_register(
        positions_matrix, rect_limits,
        f"{name}_H_{center_x:.2f}_{start_y:.2f}_{color}"
    )

    # ---------------------------
    # HOJA
    # ---------------------------
    if current_index == len(all_pore_data) - 1:
        return

    # ---------------------------
    # CONTINUACIÓN HORIZONTAL (Recursión)
    # ---------------------------
    next_index = current_index + 1
    draw_horizontal_branch(
        ax,
        (next_x, start_y, draw_w, draw_h),
        all_pore_data,
        next_index,
        positions_matrix,
        direction
    )

    # ======================================================
    # RAMAS VERTICALES (BÚSQUEDA INDEPENDIENTE)
    # ======================================================
    next_pore = all_pore_data[next_index]
    w_v, h_v = compute_branch_dims(
        next_pore['w'],
        next_pore['h'],
        BRANCHING_FACTOR
    )
    
    base_x = next_x
    
    # ----------------------------------------------------
    # Definición de la dirección de desplazamiento
    # ----------------------------------------------------
    shift_sign = -1 if direction == 'left' else 1
    
    def zona_libre(cx, y1, y2):
        """Verifica si la zona vertical centrada en cx está libre en el rango y1, y2."""
        min_x = cx - w_v / 2
        max_x = cx + w_v / 2
        for (_, (ox1, ox2, oy1, oy2)) in positions_matrix.items():
            if (
                max_x > ox1 + TOLERANCE and min_x < ox2 - TOLERANCE and
                y2 > oy1 + TOLERANCE and y1 < oy2 - TOLERANCE
            ):
                return False
        return True

    def buscar_x_seguro(y1, y2, current_y):
        """
        [MODIFICADO] Busca un centro X.
        Verifica la posición inicial (base_x). Si está ocupada, se desplaza
        UNA SOLA VEZ por w_v y, si hay desplazamiento, reduce Y por h_v.
        Retorna (cx, new_start_y).
        """
        cx = base_x
        
        if zona_libre(cx, y1, y2):
            # Posición inicial libre, usarla. No se modifica Y.
            # print(f"    [X-SEARCH] Initial X {cx:.2f} is free. Y remains {current_y:.2f}.")
            return cx, current_y
        else:
            # Posición inicial ocupada. Desplazar una vez por w_v y modificar Y.
            cx_shifted = base_x + shift_sign * (w_v*1.5)
            
            # NUEVA REGLA: Start_y se modifica sumándole el alto del cuadrado (h_v)
            new_start_y = current_y + (h_v*1.5)
            
            # print(f"    [X-SEARCH] Initial X {base_x:.2f} is blocked. Shifting X to {cx_shifted:.2f}. New Y: {current_y:.2f} -> {new_start_y:.2f} (Added {h_v:.2f}).")
            
            return cx_shifted, new_start_y

    # ---------------------------
    # VERTICAL SUPERIOR
    # ---------------------------
    y_top_min = start_y + draw_h
    y_top_max = start_y + draw_h + h_v
    
    # Se llama a buscar_x_seguro y se recuperan el nuevo X y el nuevo Y de origen
    cx_up, new_start_y_up = buscar_x_seguro(y_top_min, y_top_max, start_y)

    if cx_up is not None:
        draw_vertical_branch(
            ax,
            # Se usa el nuevo Y de origen + draw_h para la rama superior
            (cx_up, new_start_y_up + draw_h, 0, w_v), 
            all_pore_data,
            next_index,
            positions_matrix,
            direction_v=1
        )
    # else:
    #     print(f"[WARN] Vertical superior bloqueada en {name} I={current_index} (Error lógico/de dependencia)")

    # ---------------------------
    # VERTICAL INFERIOR
    # ---------------------------
    y_down_min = start_y - h_v
    y_down_max = start_y # El borde superior del rectángulo inferior es start_y
    
    # Se llama a buscar_x_seguro y se recuperan el nuevo X y el nuevo Y de origen
    cx_down, new_start_y_down = buscar_x_seguro(y_down_min, y_down_max, start_y)

    if cx_down is not None:
        draw_vertical_branch(
            ax,
            # Se usa el nuevo Y de origen para la rama inferior
            (cx_down, new_start_y_down, 0, w_v),
            all_pore_data,
            next_index,
            positions_matrix,
            direction_v=-1
        )
    # else:
    #     print(f"[WARN] Vertical inferior bloqueada en {name} I={current_index} (Error lógico/de dependencia)")

# ============================================================
# ---------------------- MANEJO DE DATOS ----------------------
# ============================================================

def leer_excel_a_rects(ruta):
    """
    Lee la hoja RESULTADOS_BET con formato:
    Pore Type | Value

    - Convierte coma decimal a punto
    - Ignora 'Micro'
    - Convierte 'nd' a 0
    - Mantiene orden canónico
    """

    if not os.path.exists(ruta):
        raise FileNotFoundError(f"No existe: {ruta}")

    df = pd.read_excel(
        ruta,
        sheet_name="RESULTADOS_BET",
        dtype=str
    )

    # Normalizar columnas
    df.columns = [c.strip() for c in df.columns]

    if "Pore Type" not in df.columns or "Value" not in df.columns:
        raise ValueError("La hoja RESULTADOS_BET debe tener columnas 'Pore Type' y 'Value'")

    # Limpiar datos
    df["Pore Type"] = df["Pore Type"].str.strip()
    df["Value"] = df["Value"].str.strip()

    # nd → 0
    df["Value"] = df["Value"].replace("nd", "0")

    # coma decimal → punto
    df["Value"] = df["Value"].str.replace(",", ".", regex=False)
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce").fillna(0)

    mapeo_nombres = {
    "Cylindrical": ["Cylindrical", "Cilíndrico", "Cilindrico"],
    "Plate": ["Plate", "Placa"],
    "Bottle Ink": ["Bottle Ink", "Cuello de Botella", "Botella"],
    "Unclassified": ["Unclassified", "Nodiferenciados", "No diferenciados"],
    "Micropores": ["Micropores", "Microporos", "Microporo"]
     }



    rects = []
    valores = []

    for nombre_interno, variantes in mapeo_nombres.items():
        # Buscamos si alguna de las variantes existe en la columna 'Pore Type'
        fila = df[df["Pore Type"].isin(variantes)]
        
        if not fila.empty:
            v = float(fila.iloc[0]["Value"])
            if v > 0:
               rects.append((nombre_interno, v, v))
               valores.append(v)

        else:
            print(f"[WARN] Ninguna variante de {nombre_interno} encontrada en el Excel.")

    return rects, valores



def generar_gama_colores(valores, cmap_name="viridis"):
      """Genera una gama de colores basada en los valores de la columna 'Valor Clave'."""
      if not valores:
            return []

      vmin, vmax = min(valores), max(valores)
      norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
      cmap = cm.get_cmap(cmap_name)

      if vmin == vmax:
            return [cmap(0.5) for _ in valores]

      return [cmap(norm(v)) for v in valores]

# ============================================================
# ---------------------- INICIO DEL DIBUJO --------------------
# ============================================================

def place_rects(ax, pore_data_full):
      """Inicia el dibujo con el primer tipo de poro (Cylindrical) y lo ramifica en V, L, R."""
      global ALL_RECTS
      # ALL_RECTS = [] # Reiniciar la lista global - Se hace en fmain
      
      if not pore_data_full:
            return
            
      positions_matrix = {} # Matriz para rastrear los bounding boxes
            
      p0 = pore_data_full[0]
      
      # 1. Dibujar el segmento base (Cylindrical, I=0) en (0, 0)
      # Nota: Este es el inicio del fractal, separado de los bloques de referencia
      root_w, root_h = p0['w'], p0['h']
      rect_bounds_root = draw_rect(ax, 0, 0, root_w, root_h, p0['name'], p0['color'])
      check_collision_and_register(positions_matrix, rect_bounds_root, p0['name'])
      
      next_index = 1
      
      if next_index >= len(pore_data_full):
            return

      p1_w_base = pore_data_full[next_index]['w']
      # p1_thickness_H = p1_w_base * THICKNESS_FACTOR # Grosor H
      
      # --- A) Ramas Verticales I=1 (Se dibujan PRIMERO y se REGISTRAN) ---
      
      # 1.1) Rama Vertical Hacia Arriba
      draw_vertical_branch(
            ax, (0, root_h, 0, root_w), 
            pore_data_full, next_index,
            positions_matrix,
            direction_v=1
      )

  
      
      # --------------------------------------------------
      # B) LÓGICA DE DETECCIÓN DE COLISIÓN Y AJUSTE DE POSICIÓN Y 
      #    PARA LAS RAMAS HORIZONTALES (I=1) - Para evitar colisión con ramas verticales I=1
      # --------------------------------------------------
      
      draw_w, draw_h = compute_branch_dims(p1_w_base, pore_data_full[next_index]['h'], BRANCHING_FACTOR)
      
      # Posición Y inicial centrada
      start_y_base_h_initial = root_h / 2 - draw_h / 2 # Usar draw_h ajustado
      current_offset_y = 0.0 # El offset se irá incrementando (moviendo hacia arriba)
      start_y_final = start_y_base_h_initial
      found_safe_position_h = False
      
      # Nota: Para las ramas H I=1, las movemos HACIA ARRIBA para evitar las ramas V inferiores (I=1)
      
      for attempt in range(COLLISION_MAX_ATTEMPTS * 2): 
            
            start_y_test = start_y_base_h_initial + current_offset_y
            
            # 1. PRUEBA DE COLISIÓN PARA EL LADO IZQUIERDO (L)
            start_x_left = -root_w / 2
            center_x_L = start_x_left - draw_w / 2 
            
            min_x_L_test = center_x_L - draw_w / 2
            max_x_L_test = center_x_L + draw_w / 2
            min_y_test = start_y_test 
            max_y_test = start_y_test + draw_h

            # 2. PRUEBA DE COLISIÓN PARA EL LADO DERECHO (R)
            start_x_right = root_w / 2
            center_x_R = start_x_right + draw_w / 2 

            min_x_R_test = center_x_R - draw_w / 2
            max_x_R_test = center_x_R + draw_w / 2
            
            is_safe = True
            
            for existing_name, (min_x_old, max_x_old, min_y_old, max_y_old) in positions_matrix.items():
                    
                    # Chequeo Lado Izquierdo (L)
                    if (max_x_L_test > min_x_old + TOLERANCE and min_x_L_test < max_x_old - TOLERANCE and
                        max_y_test > min_y_old + TOLERANCE and min_y_test < max_y_old - TOLERANCE):
                            is_safe = False
                            break
                    
                    # Chequeo Lado Derecho (R)
                    if (max_x_R_test > min_x_old + TOLERANCE and min_x_R_test < max_x_old - TOLERANCE and
                        max_y_test > min_y_old + TOLERANCE and min_y_test < max_y_old - TOLERANCE):
                            is_safe = False
                            break
                            
            if is_safe:
                  start_y_final = start_y_test # Guarda la posición Y segura
                  found_safe_position_h = True
                  break
            
            # Si hay colisión, ajustamos el offset (empujamos las ramas HACIA ARRIBA)
            current_offset_y += draw_h * COLLISION_STEP 
            
      if not found_safe_position_h:
            print("[WARN] No se encontró posición Y segura para las ramas horizontales I=1.")
      
      # print(f"[DEBUG] Posición Y inicial de ramas H I=1 ajustada con offset: {current_offset_y:.2f}")

      # --------------------------------------------------
      # C) Dibujo final de Ramas Horizontales (I=1) usando start_y_final
      # --------------------------------------------------

      # 2. Rama Izquierda: Inicia en el borde izquierdo de Cylindrical
      start_x_left = -root_w / 2
      draw_horizontal_branch(
            ax, (start_x_left, start_y_final, 0, draw_h), # Usamos draw_h real para el parent_info
            pore_data_full, next_index,
            positions_matrix,
            direction='left'
      )
      
      # 3. Rama Derecha: Inicia en el borde derecho de Cylindrical
      start_x_right = root_w / 2
      draw_horizontal_branch(
            ax, (start_x_right, start_y_final, 0, draw_h), # Usamos draw_h real para el parent_info
            pore_data_full, next_index,
            positions_matrix,
            direction='right'
      )

# ============================================================
# ---------------------- FUNCIÓN PRINCIPAL --------------------
# ============================================================

def fmain(ruta_excel, output_file="fractal_poros_final.png"):
    global ALL_RECTS
    ALL_RECTS = []
    
    fig = plt.figure(figsize=(14, 10))
    # Definimos un layout donde el fractal ocupa la mayor parte
    ax = fig.add_axes([0.05, 0.05, 0.9, 0.9]) 
    ax.set_aspect("equal")
    ax.axis('off')

    # Cargar datos
    rects_raw, valores = leer_excel_a_rects(ruta_excel)
    
    # Configuración visual
    VISUAL_SCALE = 3000
    pore_data = []
    cmap = cm.get_cmap("viridis")
    norm = mcolors.Normalize(min(valores), max(valores))

    for i, (name, v_w, v_h) in enumerate(rects_raw):
        color = 'sienna' if name == "Unclassified" else cmap(norm(v_w))
        pore_data.append({
            'name': name,
            'w': np.sqrt(v_w) * VISUAL_SCALE,
            'h': np.sqrt(v_h) * VISUAL_SCALE,
            'color': color,
            'val': v_w
        })

    # Dibujo del Fractal (Simplificado para el ejemplo)
    positions_matrix = {}
    p0 = pore_data[0]
    root_bounds = draw_rect(ax, 0, 0, p0['w'], p0['h'], p0['name'], p0['color'])
    check_collision_and_register(positions_matrix, root_bounds, p0['name'])

    # --- AGREGAR PIE CHART EN EL RINCÓN INFERIOR DERECHA ---
    # Creamos un nuevo eje para el gráfico de pastel
    ax_pie = fig.add_axes([0.7, 0.05, 0.25, 0.25]) # [x, y, ancho, alto]
    
    labels = [f"{p['name']}\n({RANGOS_NM.get(p['name'], 'nd')})" for p in pore_data]
    sizes = [p['val'] for p in pore_data]
    colors = [p['color'] for p in pore_data]

    wedges, texts, autotexts = ax_pie.pie(
        sizes, 
        labels=labels, 
        autopct='%1.1f%%',
        startangle=140,
        colors=colors,
        textprops={'fontsize': 8, 'weight': 'bold'},
        pctdistance=0.8
    )
    plt.setp(autotexts, size=7, color="white")
    ax_pie.set_title("Distribución de Poros", fontsize=10, pad=10, weight='bold')

    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Imagen guardada como {output_file}")

# --- Ejecución ---
if __name__ == "__main__":
    # Asegúrate de que el nombre del archivo coincida con tu Excel
    fmain("RESULTADOS.xlsx")
    if len(sys.argv) < 2:
        print(" Uso incorrecto")
        print("Uso correcto: python draw.py archivo.xlsx")
        sys.exit(1)

    ruta_excel = sys.argv[1]
    fmain(ruta_excel)
    