from pywinauto import Application
import time

# ==========================
# Rutas
# ==========================
PATH_NOVAWIN = r"C:\Quantachrome Instruments\NovaWin\novawin.exe"
PATH_QPS    = r"C:\Users\6lady\OneDrive\Escritorio\PRACTICAUDEC\python\qps\test.qps"
EXPORT_CSV  = r"C:\Users\6lady\OneDrive\Escritorio\PRACTICAUDEC\python\reports\hk.csv"

# ==========================
# Lanzar NovaWin
# ==========================
app = Application(backend="win32").start(PATH_NOVAWIN)
main_win = app.window(title_re=".*NovaWin.*")
main_win.wait("ready", timeout=10)

# ==========================
# Abrir archivo QPS
# ==========================
main_win.menu_select("File->Open")
open_dlg = app.window(title_re=".*Open.*")
open_dlg.wait("exists ready", timeout=5)
open_dlg.Edit.set_text(PATH_QPS)
open_dlg.Open.click()

# ==========================
# Exportar HK
# ==========================
main_win.menu_select("Tables->HK")
save_dlg = app.window(title_re=".*Save As.*")
save_dlg.wait("exists ready", timeout=5)
save_dlg.Edit.set_text(EXPORT_CSV)
save_dlg.Save.click()

# ==========================
# Cerrar NovaWin
# ==========================
main_win.close()
