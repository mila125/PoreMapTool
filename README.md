pasos para instalar PoreMap
Crear entorno virtual:
  py -3.14 -m venv venv
Activar:
  venv\Scripts\activate
Instalar requirimientos:
  pip install -r requirements.txt
Ejecuta las migración siempre con:
  python manage.py migrate
Correr PoreMap con:
  python manage.py runserver
