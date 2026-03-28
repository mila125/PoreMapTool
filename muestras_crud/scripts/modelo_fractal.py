import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import pandas as pd
import os
import glob
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
from matplotlib.path import Path
import pathlib  # <-- nuevo import
#from matplotlib.patches import PathPatch
from matplotlib.patches import PathPatch
import warnings
import numpy as np
from scipy.spatial import ConvexHull
import alphashape
from shapely.geometry import Polygon, MultiPolygon
import sys
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import logging
logger = logging.getLogger(__name__)
# Clasificación de tamaños de poro (nm)
size_classification = {
    "Plate": "3.6-36 nm",
    "Unclassified": "2-3.6 nm",
    "Micropores": "1.5-2 nm",
    "Cylindrical": "nd",
    "Bottle Ink": "nd"
}

# ============================================================
# ---------------------- CONFIGURACIÓN GLOBAL ------------------------
# ============================================================
MAX_LEVEL_PORE_TYPES = 5
VISUAL_SCALE = 3000
VISUAL_SCALE_W = 3000
VISUAL_SCALE_H = 3000
LEAF_SIZE_FACTOR = 0.15
BRANCHING_FACTOR = 3  # Valor K para la ramificación
AREA_CONSERVATION_FACTOR = 1.0 / np.sqrt(BRANCHING_FACTOR)
LENGTH_FACTOR = 0.35
COLLISION_STEP = 0.1    # Fracción en la que se reduce/incrementa el coeficiente
COLLISION_MAX_ATTEMPTS = 5 # Número máximo de veces para ajustar posición
ALL_RECTS = []
TOLERANCE = 1.5 # Tolerancia de píxeles para detectar colisión
PARENT_HEIGHT_STACK = []
# ============================================================
# ---------------------- FUNCIONES AUXILIARES ------------------------
# ============================================================

import logging
import sys
import pathlib

def setup_logging(force=True):
    SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
    LOGS_DIR = SCRIPT_DIR / "logs"
    LOGS_DIR.mkdir(exist_ok=True)
    LOG_FILE = LOGS_DIR / "proceso_novawin.log"

    root = logging.getLogger()
    if force:
        for h in root.handlers[:]:
            root.removeHandler(h)

    root.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s.%(msecs)03d | %(levelname)s | %(name)s | %(message)s",
        "%Y-%m-%d %H:%M:%S"
    )

    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)

    root.addHandler(fh)
    root.addHandler(ch)

    logging.getLogger("PIL").setLevel(logging.WARNING)
    root.info(f"Logging inicializado correctamente. Log file: {LOG_FILE}")


def log(msg, level="info"):
    """
    Usa siempre el logger raíz configurado por setup_logging().
    """
    logger = logging.getLogger()  # logger raíz
    level = level.lower()
    if level == "debug":
        logger.debug(msg)
    elif level in ("warn", "warning"):
        logger.warning(msg)
    elif level == "error":
        logger.error(msg)
    elif level == "critical":
        logger.critical(msg)
    elif level == "success":
        logger.info(f"[SUCCESS] {msg}")
    else:
        logger.info(msg)
def compute_total_branches_per_level(max_level, branching_factor):
      """Calcula el número total de ramas por nivel, aunque no se usa directamente en el dibujo."""
      branches = {}
      branches[0] = 1
      for i in range(1, max_level):
            branches[i] = branches[i-1] * branching_factor
      return branches

def compute_branch_dims(area, level, k, visual_scale=1.0):
    """
    Calcula ancho y alto de una rama:
    area_n = area / k^level
    lado = sqrt(area_n)
    """
    area_n = area / (k ** level)
    side = np.sqrt(area_n) * visual_scale
    return side, side

# ============================================================
# ---------------------- DIBUJO BÁSICO Y COLISIÓN ------------------------
# ============================================================

def draw_rect(ax, x, y, w, h, name, color, is_leaf=False):
      # Dibuja el rectángulo centrado en X, con la base en Y
      if w < 0:
            x += w
            w = abs(w)
      if h < 0:
            y += h
            h = abs(h)

      rect = Rectangle(
            (x - w / 2, y), # Punto de inicio (bottom-left)
            w,
            h,
            facecolor=color,
            edgecolor="black",
            linewidth=0.5 if is_leaf else 1
      )
      ax.add_patch(rect)
      
      # Devuelve el bounding box del rectángulo dibujado
      return x - w / 2, x + w / 2, y, y + h

def check_collision_and_register(positions_matrix, rect_bounds, name):
      """
      Verifica si el nuevo rectángulo colisiona con cualquier rectángulo ya registrado. 
      Si no hay colisión, lo registra. Devuelve True si NO hay colisión.
      """
      global ALL_RECTS
      
      min_x_new, max_x_new, min_y_new, max_y_new = rect_bounds
      
      for existing_name, (min_x_old, max_x_old, min_y_old, max_y_old) in positions_matrix.items():
            # Si hay superposición en X Y en Y (más la tolerancia)
            if (max_x_new > min_x_old + TOLERANCE and min_x_new < max_x_old - TOLERANCE and
                  max_y_new > min_y_old + TOLERANCE and min_y_new < max_y_old - TOLERANCE):
                  # Hay colisión
                  return False
                  
      # Si no hubo colisión, registramos la nueva posición
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
    name = pore['name']
    area = pore['area']
    color = pore['color']
    level = current_index

    draw_w, draw_h = compute_branch_dims(
      area,
     level,
     BRANCHING_FACTOR,
     visual_scale=VISUAL_SCALE_W
    )

    # ---------------------------------
    # DATOS DEL PADRE
    # ---------------------------------
    px_parent, py_anchor, _, _ = parent_info

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
                # log("no solapa!")
                continue

            # ---------------------------------
            # MISMO COLOR → mover X
            # ---------------------------------
            # Nota: La key de positions_matrix ahora incluye el color, 
            # permitiendo distinguir el solape por tipo de poro.
            if key.endswith(f"_{color}"):
                # log("mismo color!")
                blocked = True
                break

            # ---------------------------------
            # COLOR DISTINTO → prohibido
            # ---------------------------------
            # log("distinto!")
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

    next_w, next_h = compute_branch_dims(
        next_pore['area'],
        next_index,
        BRANCHING_FACTOR,
        visual_scale=VISUAL_SCALE_W
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
        (center_x, next_anchor_y, draw_w, draw_h),
        all_pore_data,
        next_index,
        positions_matrix,
        direction_v=direction_v
    )

    # ---------------------------------
    # RAMAS HORIZONTALES
    # ---------------------------------
    mid_y = start_y + draw_h / 2
    start_y_h = mid_y - next_h / 2

    draw_horizontal_branch(
        ax,
        (center_x - half_w, start_y_h, 0, next_h),
        all_pore_data,
        next_index,
        positions_matrix,
        direction='left'
    )

    draw_horizontal_branch(
        ax,
        (center_x + half_w, start_y_h, 0, next_h),
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
    name = pore['name']
    area = pore['area']
    color = pore['color']
    level = current_index

    draw_w, draw_h = compute_branch_dims(
     area,
     level,
     BRANCHING_FACTOR,
     visual_scale=VISUAL_SCALE_W
    )

    # ---------------------------
    # DATOS DEL PADRE (solo posición)
    # ---------------------------
    px_parent_end, start_y, _, _ = parent_info
    anchor_y = start_y        # Y REAL del padre (NO se toca jamás)
    draw_y   = start_y        # Y solo para dibujar el rectángulo horizontal

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
            draw_y = y_test
            # log(f"  [INFO] H-Branch Y-Adjust: {initial_y:.2f} -> {start_y:.2f} (Offset: {y_offset:.2f})")
            break

        y_offset += draw_h * COLLISION_STEP
        if _ == COLLISION_MAX_ATTEMPTS * 2 - 1:
            # log(f"  [WARN] Horizontal Y-collision failed for {name}. Using original Y.")
            pass


    # ---------------------------
    # DIBUJO HORIZONTAL
    # ---------------------------
    rect_limits = draw_rect(
    ax, center_x, draw_y, draw_w, draw_h,
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
    next_area = next_pore['area']
    next_level = next_index

    w_v, h_v = compute_branch_dims(
        next_area,
        next_level,
        BRANCHING_FACTOR,
        VISUAL_SCALE
    )
    
    base_x = center_x
    
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
      cx = base_x

      if zona_libre(cx, y1, y2):
          return cx, current_y

      cx_shifted = base_x + shift_sign * (w_v * 1.5)

      if zona_libre(cx_shifted, y1, y2):
          return cx_shifted, current_y

      return base_x, current_y

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
          (cx_up, anchor_y + draw_h, 0, w_v), # anchor_y + draw_h es el techo del segmento
          all_pore_data,
          next_index,
          positions_matrix,
          direction_v=1
        )
    # else:
    #     log(f"[WARN] Vertical superior bloqueada en {name} I={current_index} (Error lógico/de dependencia)")

    # ---------------------------
    # VERTICAL INFERIOR
    # ---------------------------
    y_down_min = start_y - h_v
    y_down_max = start_y # El borde superior del rectángulo inferior es start_y
    
    # Se llama a buscar_x_seguro y se recuperan el nuevo X y el nuevo Y de origen
    cx_down, new_start_y_down = buscar_x_seguro(y_down_min, y_down_max, start_y)

    if cx_down is not None:
        # Para la Vertical Inferior
        draw_vertical_branch(
          ax,
          (cx_down, anchor_y, 0, w_v), # anchor_y es la base del segmento
          all_pore_data,
          next_index,
          positions_matrix,
          direction_v=-1
      )
    # else:
    #     log(f"[WARN] Vertical inferior bloqueada en {name} I={current_index} (Error lógico/de dependencia)")

# ============================================================
# ---------------------- MANEJO DE DATOS ----------------------
# ============================================================

def leer_excel_a_rects(ruta):
    """
    Lee la hoja RESULTADO_CALCULOS con formato:
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
        sheet_name="RESULTADO_POROS",
        dtype=str
    )

    # Normalizar columnas
    df.columns = [c.strip() for c in df.columns]

    if "Pore Type" not in df.columns or "Value" not in df.columns:
        raise ValueError("La hoja RESULTADO_POROS debe tener columnas 'Pore Type' y 'Value'")

    # Limpiar datos
    df["Pore Type"] = df["Pore Type"].str.strip()
    df["Value"] = df["Value"].str.strip()

    # nd → 0
    df["Value"] = df["Value"].replace("nd", "0")

    # coma decimal → punto
    df["Value"] = df["Value"].str.replace(",", ".", regex=False)
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce").fillna(0)

    mapeo_nombres = {
    "Cylindrical": ["Cylindrical", "BET_C", "Cilindrico"],
    "Plate": ["Plate", "BET_P","Placa"],
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
            log(f"[WARN] Ninguna variante de {nombre_interno} encontrada en el Excel.")

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
      root_side = np.sqrt(p0['area']) * VISUAL_SCALE
      root_w = root_h = root_side
      rect_bounds_root = draw_rect(ax, 0, 0, root_w, root_h, p0['name'], p0['color'])
      check_collision_and_register(positions_matrix, rect_bounds_root, p0['name'])
      
      next_index = 1
      
      if next_index >= len(pore_data_full):
            return

      p1_area = pore_data_full[next_index]['area']
      # p1_thickness_H = p1_w_base * AREA_CONSERVATION_FACTOR # Grosor H
      
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
      
      p1_area = pore_data_full[next_index]['area']

      draw_w, draw_h = compute_branch_dims(
        p1_area,
        next_index,
        BRANCHING_FACTOR,
        VISUAL_SCALE
    )
      
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
            log("[WARN] No se encontró posición Y segura para las ramas horizontales I=1.")
      
      # log(f"[DEBUG] Posición Y inicial de ramas H I=1 ajustada con offset: {current_offset_y:.2f}")

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


def fmain(ruta_excel, output_dir="fractal", output_file=None):
    """
    Genera un fractal de poros a partir de un archivo Excel.
    
    Parámetros:
        ruta_excel (str | Path): Ruta del archivo Excel con los datos.
        output_dir (str | Path): Carpeta donde guardar la imagen (se crea junto al Excel si no existe).
        output_file (str): Nombre final del PNG. Si no se da, se genera a partir del nombre del Excel.
    
    Retorna:
        Path: Ruta completa al PNG generado.
    """
    from pathlib import Path
    import os
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np

    log("Fractal: inicio fmain")
    log(f"Excel recibido: {ruta_excel}")
    log(f"Output dir: {output_dir}")

    global ALL_RECTS
    ALL_RECTS = []

    # ------------------------------------------------------------
    # Convertir ruta a Path y validar existencia
    # ------------------------------------------------------------
    ruta_excel = Path(ruta_excel)
    if not ruta_excel.exists():
        log(f"[ERROR] El archivo no existe: {ruta_excel}")
        return None

    # Generar nombre de archivo si no se pasó
    if output_file is None:
        output_file = f"{ruta_excel.stem}_fractal.png"

    # Crear carpeta de salida al mismo nivel que el Excel
    SCRIPT_DIR = Path(__file__).resolve().parent
    carpeta_salida = SCRIPT_DIR / "fractal"
    carpeta_salida.mkdir(parents=True, exist_ok=True)

    ruta_final = carpeta_salida / output_file

    # ------------------------------------------------------------
    # CONFIGURACIÓN INICIAL DEL GRÁFICO
    # ------------------------------------------------------------
    UNCLASSIFIED_GROUP_X = -5
    fig, ax = plt.subplots(figsize=(12, 16))
    ax.set_aspect("equal")

    # ------------------------------------------------------------
    # LECTURA DEL EXCEL
    # ------------------------------------------------------------
    try:
        rects, valores = leer_excel_a_rects(str(ruta_excel))  # asegurar string si la función lo necesita

        # Evitar float() sobre strings no numéricos
        valores_float = []
        for v in valores:
            try:
                valores_float.append(float(v))
            except (ValueError, TypeError):
                log(f"[WARN] Valor no numérico encontrado y convertido a 0: {v}")
                valores_float.append(0.0)
        valores = valores_float

        log(f"[INFO] Archivo Excel cargado correctamente: {ruta_excel}")
    except Exception as e:
        log(f"[ERROR] Fractal falló al leer el Excel: {e}")
        return None

    # ------------------------------------------------------------
    # PREPARAR DATOS DE POROS
    # ------------------------------------------------------------
    colores = generar_gama_colores(valores, cmap_name="viridis")
    pore_data_full = []

    unclassified_name = "Unclassified"
    distinct_unclassified_color = "sienna"

    for i, (name, v_w, v_h) in enumerate(rects):
        assigned_color = colores[i] if i < len(colores) else "gray"

        if name == unclassified_name:
            assigned_color = distinct_unclassified_color
            log(f"[INFO] Color de '{unclassified_name}' forzado a '{distinct_unclassified_color}'.")

        pore_data_full.append({
            "name": name,
            "area": v_w if isinstance(v_w, (int, float)) else 0.0,
            "color": assigned_color,
            "index": i
        })

    # ------------------------------------------------------------
    # EXTRAER CUADRADO UNCLASSIFIED (REFERENCIA)
    # ------------------------------------------------------------
    try:
        unclassified = next(item for item in pore_data_full if item["name"] == unclassified_name)
    except StopIteration:
        log("[WARN] 'Unclassified' no encontrado.")
        unclassified = {"area": 0, "color": "gray"}

    side_unclassified = np.sqrt(unclassified["area"]) * VISUAL_SCALE if unclassified["area"] > 0 else 1.0
    log(f"[INFO] Área Unclassified: {unclassified['area']}, lado visual: {side_unclassified}")

    # ------------------------------------------------------------
    # DIBUJO DEL CUADRADO BASE UNCLASSIFIED
    # ------------------------------------------------------------
    positions_matrix = {}
    yellow_limits = draw_rect(
        ax, UNCLASSIFIED_GROUP_X, 0, side_unclassified, side_unclassified,
        "Unclassified\n(Base)", unclassified["color"]
    )
    check_collision_and_register(positions_matrix, yellow_limits, "Unclassified")

    # ------------------------------------------------------------
    # DIBUJO DEL FRACTAL DE POROS
    # ------------------------------------------------------------
    place_rects(ax, pore_data_full)

    # ------------------------------------------------------------
    # LEYENDA
    # ------------------------------------------------------------
    total_valor = sum(v for v in valores if v > 0)
    legend_patches = []

    for i, data in enumerate(pore_data_full):
        name = data["name"]
        color = data["color"]
        valor_real = valores[i] if i < len(valores) else 0.0
        rango = size_classification.get(name, "—")
        pct_txt = f"{(valor_real / total_valor * 100):.1f} %" if total_valor > 0 else "nd"

        label = f"{name}\nRango: {rango}\nÁrea/Volumen: {valor_real:.4f}\nFracción: {pct_txt}"
        legend_patches.append(mpatches.Patch(facecolor=color, edgecolor="black", label=label))

    if legend_patches:
        legend = ax.legend(
         handles=legend_patches,
         loc="upper left",
         bbox_to_anchor=(0.92, 0.98),
         ncol=1,
         frameon=False,              # ❌ sin cuadro
         title="Clasificación de Poros\n(Tamaño y Fracción)",
         fontsize=14,                # 🔠 texto más grande
         title_fontsize=16,          # 🔠 título más grande
         handlelength=2.5,
         labelspacing=1.6
)

    ax.set_axis_off()

    # ------------------------------------------------------------
    # AJUSTE DE LÍMITES
    # ------------------------------------------------------------
    if ALL_RECTS:
        all_x = [r[0] for r in ALL_RECTS] + [r[1] for r in ALL_RECTS]
        all_y = [r[2] for r in ALL_RECTS] + [r[3] for r in ALL_RECTS]
        margin_x = (max(all_x) - min(all_x)) * 0.1
        margin_y = (max(all_y) - min(all_y)) * 0.1
        ax.set_xlim(min(all_x) - margin_x, max(all_x) + margin_x)
        ax.set_ylim(min(all_y) - margin_y, max(all_y) + margin_y)

    # ------------------------------------------------------------
    # GUARDADO FINAL
    # ------------------------------------------------------------
    plt.savefig(ruta_final, dpi=300, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)

    log(f"[SUCCESS] Imagen generada correctamente en: {ruta_final}")
    return ruta_final
# --- Ejecución ---
import tkinter as tk
from tkinter import messagebox

if __name__ == "__main__":
    setup_logging()
    log("Inicio del fractal")

    if len(sys.argv) < 2:
        log("No se recibió archivo Excel, usando ejemplo de prueba.", "warn")
        ruta_excel = "test_report_56.xlsx"  #  fallback
    else:
        ruta_excel = sys.argv[1]

    try:
        fmain(ruta_excel)
    except Exception as e:
        log(f"Error en fmain: {e}", "error")

        # ----------------------------
        # Mostrar error en un msgbox
        # ----------------------------
        root = tk.Tk()
        root.withdraw()  # Oculta la ventana principal
        messagebox.showerror("Error en Fractal", str(e))
        root.destroy()

        sys.exit(1)
        fmain(ruta_excel)
    except Exception as e:
        log(f"Error en fmain: {e}", "error")
        sys.exit(1)
    