from django.apps import AppConfig


class MuestrasCrudConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'muestras_crud'
from django.contrib.auth.apps import AuthConfig

class CustomAuthConfig(AuthConfig):
    verbose_name = "Authentication"