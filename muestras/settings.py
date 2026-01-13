"""
Django settings para muestras listo para PyInstaller
"""

import sys
import os
from pathlib import Path

# ==========================
# 1️⃣ Base Directory
# ==========================
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys._MEIPASS)  # PyInstaller runtime folder (solo lectura)
    TEMP_DIR = Path(os.getenv("TEMP", Path.home() / "AppData/Local/Temp")) / "muestras_app"
else:
    BASE_DIR = Path(__file__).resolve().parent.parent
    TEMP_DIR = BASE_DIR / "temp"

TEMP_DIR.mkdir(parents=True, exist_ok=True)

# ==========================
# 2️⃣ Seguridad
# ==========================
SECRET_KEY = "django-insecure-eps@2isixj+!8*or0%$xes4evvs+nnxy%$2+#!)hk+dk+gf+*$"
DEBUG = not getattr(sys, "frozen", False)  # True mientras depuras el .exe
ALLOWED_HOSTS = ["*", "localhost", "127.0.0.1"]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = ["*"]

X_FRAME_OPTIONS = "SAMEORIGIN"
SILENCED_SYSTEM_CHECKS = ["security.W019"]

# ==========================
# 3️⃣ Apps
# ==========================
INSTALLED_APPS = [
    "admin_interface",
    "colorfield",
    "django.contrib.admin",
    "muestras_crud.apps.CustomAuthConfig",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "muestras_crud",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "muestras.urls"

WSGI_APPLICATION = "muestras.wsgi.application"

# ==========================
# 4️⃣ Templates y Static
# ==========================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "muestras_crud" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "muestras_crud" / "static"]
STATIC_ROOT = TEMP_DIR / "staticfiles"

# ==========================
# 5️⃣ Media y Archivos Generados
# ==========================
MEDIA_URL = "/media/"
MEDIA_ROOT = TEMP_DIR / "media"
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

PDF_DIR = TEMP_DIR / "pdftables"
PDF_DIR.mkdir(parents=True, exist_ok=True)

RUTA_TABLES_EXCEL = PDF_DIR / "tables.xlsx"
RUTA_FIRMA_PNG = PDF_DIR / "firma.png"
RUTA_ANEXOS_DIR = PDF_DIR / "anexos"
RUTA_ANEXOS_DIR.mkdir(exist_ok=True)

LOG_DIR = TEMP_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

# ==========================
# 6️⃣ Base de datos
# ==========================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": TEMP_DIR / "db.sqlite3",
    }
}

# ==========================
# 7️⃣ Password validators
# ==========================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ==========================
# 8️⃣ Internacionalización
# ==========================
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ==========================
# 9️⃣ Logging
# ==========================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{levelname} {asctime} {module} {message}", "style": "{"},
        "simple": {"format": "{levelname} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_FILE),
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 3,
            "formatter": "verbose",
        },
    },
    "root": {"handlers": ["console", "file"], "level": "DEBUG"},
}