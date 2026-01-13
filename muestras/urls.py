from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from muestras_crud import views


urlpatterns = [
    # 1. PANTALLA DE INICIO
    path('', views.splash_screen, name='home'), 
    
    # --- AÑADIR ESTA LÍNEA PARA LAS VISTAS DE AUTENTICACIÓN ---
    path("accounts/", include("django.contrib.auth.urls")), 

    # 2. Rutas que NO usan la raíz
    path("admin/pca/", views.pca_visualizacion, name="pca_visualizacion"),
    path("admin/", admin.site.urls),
    
    # Incluye las URLs de la aplicación muestras_crud (que contiene /configuracion/)
    path("", include("muestras_crud.urls")),

    # 2. Destinos de los Botones
    path('tutorial/', views.tutorial_view, name='nombre_de_tu_vista_tutorial'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)