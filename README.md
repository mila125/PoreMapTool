Requirimientos de sistema: Windows 10/11
-Python 3.11
-Anaconda
-Software NovaWin instalado
Instalación de PoreMap
1. Crear entorno (recomendado: conda)
conda create -n poremap python=3.11 -y
conda activate poremap
2. Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
3. Aplicar migraciones
python manage.py migrate
4. Crear superusuario
python manage.py createsuperuser
5. Ejecutar servidor
python manage.py runserver
