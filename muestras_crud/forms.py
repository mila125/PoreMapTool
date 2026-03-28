from django import forms
from .models import Muestra, Informe

class MuestraForm(forms.ModelForm):
    class Meta:
        model = Muestra
        fields = '__all__'

class InformeForm(forms.ModelForm):
    class Meta:
        model = Informe
        fields = ['archivo_xlsx', 'archivo_pdf']  # solo campos existentes

# forms.py

from .models import ConfiguracionInforme

class ConfiguracionInformeForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionInforme
        fields = ['tipo_ejecucion', 'archivo_qps', 'carpeta_qps']
    
    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo_ejecucion')
        archivo = cleaned_data.get('archivo_qps')
        carpeta = cleaned_data.get('carpeta_qps')

        if tipo == 'archivo' and not archivo:
            raise forms.ValidationError("Debes seleccionar un archivo QPS")
        if tipo == 'carpeta' and not carpeta:
            raise forms.ValidationError("Debes indicar la carpeta con archivos QPS")