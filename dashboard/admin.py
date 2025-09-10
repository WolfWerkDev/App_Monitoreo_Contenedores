from django.contrib import admin  # Importa el módulo de administración de Django

# Importa los modelos del Dashboard
from .models import Dispositivo, Reporte, Alerta

# Personaliza los textos del panel de administración
admin.site.site_header = "App Monitoreo"  # Texto en la cabecera del admin
admin.site.site_title = "AppMon Admin"    # Título de la pestaña del navegador
admin.site.index_title = "Bienvenido al panel de administración"  # Texto de bienvenida

# Inline para mostrar alertas dentro de un reporte
class AlertaInline(admin.TabularInline):  # Muestra alertas en forma de tabla dentro del admin del reporte
    model = Alerta  # Modelo relacionado
    extra = 1       # Cantidad de formularios vacíos para agregar nuevas alertas
    readonly_fields = ("fecha_alerta",)  # Campos de solo lectura

# Inline para mostrar reportes dentro de un dispositivo
class ReporteInline(admin.TabularInline):
    model = Reporte  # Modelo relacionado
    extra = 1        # Cantidad de formularios vacíos para agregar nuevos reportes
    readonly_fields = ("fecha",)  # Campos de solo lectura

# Admin personalizado para Dispositivo
@admin.register(Dispositivo)
class DispositivoAdmin(admin.ModelAdmin):
    list_display = ("id", "device_name")  # Campos que se muestran en la lista de dispositivos
    search_fields = ("device_name",)      # Campos por los que se puede buscar
    inlines = [ReporteInline]             # Muestra los reportes relacionados dentro del dispositivo

# Admin personalizado para Reporte
@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    list_display = ("id", "dispositivo", "medicion_nivel", "estado_puerta", "fecha")  # Columnas visibles
    list_filter = ("estado_puerta", "fecha")  # Filtros rápidos en la lista
    search_fields = ("dispositivo__device_name",)  # Búsqueda por nombre de dispositivo relacionado
    inlines = [AlertaInline]  # Muestra las alertas relacionadas dentro del reporte

# Admin personalizado para Alerta
@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ("id", "reporte", "mensaje", "is_activa", "fecha_alerta", "fecha_desactivada")  # Columnas visibles
    list_filter = ("fecha_alerta",)  # Filtro por fecha de alerta
    search_fields = ("mensaje", "reporte__dispositivo__device_name")  # Búsqueda por mensaje o nombre de dispositivo del reporte
