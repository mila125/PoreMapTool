# -----------------------------
# models.py
# -----------------------------
from django.db import models



class ConfiguracionInforme(models.Model):
    tipo_ejecucion = models.CharField(
        max_length=50,
        choices=[
            ('manual', 'Manual'),
            ('automatica', 'Automática'),
        ],
        default='manual'
    )
    archivo_qps = models.FileField(upload_to='qps/', blank=True, null=True)
    carpeta_qps = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Configuración ({self.tipo_ejecucion})"

class Empresa(models.Model):
 nombre = models.CharField(max_length=250)
 encargado = models.CharField(max_length=250, blank=True, null=True)


 def __str__(self):
  return self.nombre




class Muestra(models.Model):
 empresa = models.ForeignKey(Empresa, on_delete=models.SET_NULL, null=True, blank=True)
 sample_number = models.CharField(max_length=100)


 def __str__(self):
  return f"{self.sample_number} - {self.empresa}"



# models.py
class Informe(models.Model):
    muestra = models.ForeignKey(Muestra, on_delete=models.CASCADE)
    fecha = models.DateField(auto_now_add=True)
    archivo_xlsx = models.FileField(upload_to='informes/xlsx/', blank=True, null=True)
    archivo_pdf = models.FileField(upload_to='informes/pdf/', blank=True, null=True)
    

    def __str__(self):
        return f"Informe {self.id} - {self.muestra}"

    def __str__(self):
        return f"Informe {self.id} - {self.muestra}"


class Dataset(models.Model):
    informe = models.OneToOneField(
        Informe,
        on_delete=models.CASCADE,
        primary_key=True
    )

    # ===== POROSIDAD =====
    bjh_pore_volume_avg = models.FloatField(null=True, blank=True)
    hk_volume_cc_g = models.FloatField(null=True, blank=True)
    dft_half_pore_width = models.FloatField(null=True, blank=True)
    dft_pore_volume = models.FloatField(null=True, blank=True)

    # ===== FRACTALES =====
    fhh = models.FloatField(null=True, blank=True)
    nk = models.FloatField(null=True, blank=True)

    # ===== BET =====
    single_bet = models.FloatField(null=True, blank=True)

    # ===== VOLUMEN TOTAL DE POROS =====
    volumen_total_porosidad = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Volumen total de porosidad (cc/g)"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Dataset Informe {self.informe_id}"