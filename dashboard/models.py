from django.db import models  # Importa herramientas para definir modelos en Django

# Modelo que representa un dispositivo físico o virtual
class Dispositivo(models.Model):
    device_name = models.CharField(max_length=100)  # Nombre del dispositivo

    def __str__(self):
        return self.device_name  # Representación legible del dispositivo en el admin y otros lugares

# Modelo que representa un reporte generado por un dispositivo
class Reporte(models.Model):
    dispositivo = models.ForeignKey(
        Dispositivo,  # Relación con el dispositivo que genera el reporte
        on_delete=models.CASCADE,  # Si se borra el dispositivo, se borran sus reportes
        related_name="reportes"  # Permite acceder a los reportes de un dispositivo con dispositivo.reportes
    )
    medicion_nivel = models.IntegerField()  # Nivel medido por el dispositivo (ej. nivel de líquido)
    estado_puerta = models.BooleanField()   # Estado de la puerta: True=Abierta, False=Cerrada
    fecha = models.DateTimeField(auto_now_add=True)  # Fecha y hora de creación del reporte, automático

    def __str__(self):
        # Representación legible del reporte
        return f"Reporte de {self.dispositivo} - Nivel: {self.medicion_nivel} - Puerta: {'Abierta' if self.estado_puerta else 'Cerrada'}"
    
# Modelo que representa una alerta generada a partir de un reporte
class Alerta(models.Model):
    reporte = models.ForeignKey(
        Reporte,  # Relación con el reporte que genera la alerta
        on_delete=models.CASCADE,  # Si se borra el reporte, se borran sus alertas
        related_name="alertas"  # Permite acceder a las alertas de un reporte con reporte.alertas
    )
    mensaje = models.CharField(max_length=200)  # Mensaje descriptivo de la alerta
    is_activa = models.BooleanField()  # Indica si la alerta está activa o no
    fecha_alerta = models.DateTimeField(auto_now_add=True)  # Fecha y hora de creación de la alerta
    fecha_desactivada = models.DateTimeField(null=True, blank=True)  # Fecha en que se desactivó la alerta (opcional)

    def __str__(self):
        # Representación legible de la alerta
        return f"Alerta: {self.mensaje} ({self.reporte})"
