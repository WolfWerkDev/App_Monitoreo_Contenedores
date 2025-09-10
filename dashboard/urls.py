from django.urls import path, include  # Importa herramientas para definir rutas en Django
from . import views  # Importa las vistas del mismo directorio

# Lista de URLs para la app Dashboard
urlpatterns = [
    # URL principal del dashboard
    path('', views.dashboard, name="dashboard"),  # Renderiza la vista principal del dashboard

    # URL para cargar partes del dashboard mediante peticiones AJAX o parciales
    path('dashboard/partial/', views.dashboard_partial, name="dashboard_partial"),

    # URL para recibir reportes enviados desde el ESP32
    path('esp32/', views.reporte_ESP32, name="reporte_esp32"),

    # URL para cerrar sesión del usuario
    path('logout/', views.logout_view, name='logout'),
]
