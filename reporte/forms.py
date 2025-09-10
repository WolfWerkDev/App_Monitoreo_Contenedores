from django import forms
from dashboard.models import Dispositivo

# Formulario para filtrar y generar informes
class informe(forms.Form):

    # Opciones de tipo de informe
    TIPO_INFORME_CHOICES = [
        ('reporte', 'Reporte'),
        ('alerta', 'Alerta'),
    ]

    # Opciones para filtrar por fecha
    DE_FECHA_CHOICES = [
        ('despues', 'Después de'),
        ('en', 'En'),
        ('antes', 'Antes de'),
    ]

    # Opciones para filtrar por hora
    DE_HORA_CHOICES = [
        ('despues', 'Después de las'),
        ('entre', 'Entre las ... y las ...'),
        ('antes', 'Antes de las'),
    ]

    # Opciones para el estado de alerta
    ESTADO_ALERTA_CHOICES = [
        ('', 'Seleccione una opcion'),
        ('todas', 'Todas'),
        ('activas', 'Activas'),
        ('inactivas', 'Inactivas'),
    ]

    # Campos del formulario
    dispositivos = forms.ChoiceField(label="Contenedor")
    tipo_informe = forms.ChoiceField(
        choices=[('', 'Seleccione una opción')] + TIPO_INFORME_CHOICES,
        label="Tipo de informe",
        required=False
    )
    estado_alerta = forms.ChoiceField(
        choices=ESTADO_ALERTA_CHOICES,
        label="Estado alertas",
        required=False
    )
    de_fecha = forms.ChoiceField(
        choices=[('', 'Seleccione una opción')] + DE_FECHA_CHOICES,
        label="De fecha",
        required=False
    )
    fecha = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        input_formats=['%Y-%m-%d'],
        label="Fecha",
        required=False
    )
    de_hora = forms.ChoiceField(
        choices=[('', 'Seleccione una opción')] + DE_HORA_CHOICES,
        label="De hora",
        required=False
    )
    hora1 = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'}),
        input_formats=['%H:%M'],
        label="Hora",
        required=False
    )
    hora2 = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'}),
        input_formats=['%H:%M'],
        label="Hora segunda",
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Se consulta la base de datos aquí, al instanciar el formulario
        dispositivos_choices = [('all', 'Todos')] + [(d.id, d.device_name) for d in Dispositivo.objects.all()]
        self.fields['dispositivos'].choices = dispositivos_choices
