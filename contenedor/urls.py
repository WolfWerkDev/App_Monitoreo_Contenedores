from django.urls import path, include  # Importa herramientas para definir rutas en Django
from . import views  # Importa las vistas del directorio Contenedor

# Lista de URLs para la app Contenedor
urlpatterns = [
    # URL para ver el detalle de un contenedor específico
    path('<int:id>/', views.detalle_contenedor, name='detalle_contenedor'),

    # URL para cargar partes del contenedor mediante peticiones AJAX o parciales
    path('partial/<int:device_id>/', views.contenedor_partial, name='contenedor_partial'),

    # URL para ver alertas asociadas a un contenedor específico
    path('contenedor/alertas/<int:device_id>/', views.alertas, name='alertas'),
]
