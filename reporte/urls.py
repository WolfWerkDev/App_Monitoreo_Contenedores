from django.urls import path  # Importa la función path para definir rutas
from . import views  # Importa las vistas del mismo directorio

# Definición de las rutas (URLs) para la app Reporte
urlpatterns = [
    # Página principal del reporte, muestra formulario e información
    path('', views.reporte, name='report_index'),

    # Generar un reporte en PDF
    path("reporte/pdf/", views.generar_pdf, name="generar_pdf"),
]
