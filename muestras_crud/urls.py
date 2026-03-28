# --- muestras_crud/urls.py (Corregido) ---
from django.urls import path
from . import views


urlpatterns = [
    # --- ELIMINADA: path('', views.panel_configuracion, name='panel_configuracion'), ---
    
    # --- PANEL PRINCIPAL (Ahora solo accesible por /configuracion/) ---
    path('configuracion/', views.panel_configuracion, name='panel_configuracion'), 
    
    # --- ELIMINADO el path('tutorial/') duplicado si ya lo tienes en la app principal.
    # Es mejor dejar las urls de botones de navegación global en el archivo de la app:
    path('tutorial/', views.tutorial_view, name='tutorial'),

    # --- MUESTRAS ---
    path('cargar-dataset/<int:informe_id>/', views.cargar_a_dataset, name='cargar_a_dataset'),
    path('muestras/crear/', views.crear_muestra, name='crear_muestra'),
    path('muestras/editar/<int:id>/', views.editar_muestra, name='editar_muestra'),
    path('muestras/eliminar/<int:id>/', views.eliminar_muestra, name='eliminar_muestra'),
    path('muestras/<int:muestra_id>/informe/', views.ver_informe, name='ver_informe'),
    path('muestras/<int:muestra_id>/generar/', views.generar_informe_automatico, name='generar_informe_automatico'),

    # --- INFORMES ---
    path('informes/', views.listar_informes, name='listar_informes'),
    path('informes/crear/', views.crear_informe, name='crear_informe'),
    path('informes/ejecutar/', views.ejecutar_analisis, name='ejecutar_todos_informes'),

    # --- EMPRESAS, USUARIOS, DESCARGAS ---
    path('empresas/', views.listar_empresas, name='listar_empresas'),
    path('usuarios/', views.listar_usuarios, name='listar_usuarios'),
    path('descargar/', views.descargar_archivo, name='descargar_archivo'),

    #PCA
    path("pca/", views.pca_visualizacion, name="pca_visualizacion"),
]