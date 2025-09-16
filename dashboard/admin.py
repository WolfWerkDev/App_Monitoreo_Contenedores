from django.contrib import admin
from django.conf import settings
from django.http import FileResponse
import os
import json
from datetime import datetime, timedelta
from django.utils import timezone

# Importa los modelos del Dashboard
from .models import Dispositivo, Reporte, Alerta

# =========================
# Personalización del admin
# =========================
admin.site.site_header = "App Monitoreo"
admin.site.site_title = "AppMon Admin"
admin.site.index_title = "Bienvenido al panel de administración"

# =========================
# Inlines
# =========================
class AlertaInline(admin.TabularInline):
    model = Alerta
    extra = 1
    readonly_fields = ("fecha_alerta",)

class ReporteInline(admin.TabularInline):
    model = Reporte
    extra = 1
    readonly_fields = ("fecha",)

# =========================
# Admins
# =========================
@admin.register(Dispositivo)
class DispositivoAdmin(admin.ModelAdmin):
    list_display = ("id", "device_name")
    search_fields = ("device_name",)
    inlines = [ReporteInline]

# Directorio para backups
BACKUP_DIR = os.path.join(settings.BASE_DIR, 'backups')
if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

# =========================
# Acciones del admin
# =========================
@admin.action(description="Generar backup JSON desde el primer registro hasta 60 días después")
def generar_backup(modeladmin, request, queryset=None):
    # Buscar el primer reporte existente
    primer_reporte = Reporte.objects.order_by('fecha').first()
    if not primer_reporte:
        modeladmin.message_user(request, "No hay reportes para respaldar.", level='warning')
        return

    fecha_inicio = primer_reporte.fecha
    fecha_fin = fecha_inicio + timedelta(days=60)

    reportes = Reporte.objects.filter(fecha__gte=fecha_inicio, fecha__lte=fecha_fin)

    data = []
    reportes_ids = []
    for r in reportes:
        reportes_ids.append(r.id)
        alertas = []
        if hasattr(r, 'alertas'):
            for a in r.alertas.all():
                alertas.append({
                    'mensaje': a.mensaje,
                    'is_activa': a.is_activa,
                    'fecha_alerta': timezone.localtime(a.fecha_alerta).isoformat() if a.fecha_alerta else None,
                    'fecha_desactivada': timezone.localtime(a.fecha_desactivada).isoformat() if a.fecha_desactivada else None
                })
        data.append({
            'id': r.id,
            'dispositivo': r.dispositivo.device_name if r.dispositivo else str(r.dispositivo),
            'medicion_nivel': r.medicion_nivel,
            'estado_puerta': r.estado_puerta,
            'fecha': timezone.localtime(r.fecha).isoformat() if r.fecha else None,
            'alertas': alertas
        })

    # Guardar JSON con hora local correcta
    filename = f"backup_{timezone.localtime(timezone.now()).strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(BACKUP_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    request.session['backup_ids'] = reportes_ids
    request.session['backup_file'] = filepath

    return FileResponse(open(filepath, 'rb'), as_attachment=True, filename=filename)


@admin.action(description="Eliminar registros respaldados en la última backup")
def eliminar_backup(modeladmin, request, queryset=None):
    # Obtener ids y nombre del archivo de la sesión
    backup_ids = request.session.get('backup_ids', [])
    backup_file = request.session.get('backup_file')

    if not backup_ids or not backup_file:
        modeladmin.message_user(
            request,
            "No hay backup reciente registrado para eliminar.",
            level='warning'
        )
        return

    # Eliminar alertas y reportes
    for r in Reporte.objects.filter(id__in=backup_ids):
        r.alertas.all().delete()
        r.delete()

    # Intentar borrar el archivo JSON
    try:
        if os.path.exists(backup_file):
            os.remove(backup_file)
    except Exception as e:
        modeladmin.message_user(
            request,
            f"Los registros fueron eliminados, pero no se pudo borrar el archivo: {e}",
            level='error'
        )
        # Limpiar sesión aunque haya error con el archivo
        request.session.pop('backup_ids', None)
        request.session.pop('backup_file', None)
        return

    # Limpiar la sesión
    request.session.pop('backup_ids', None)
    request.session.pop('backup_file', None)

    modeladmin.message_user(
        request,
        f"Se eliminaron {len(backup_ids)} reportes, sus alertas y el archivo de backup."
    )

# =========================
# Admin Reporte
# =========================
@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    list_display = ("id", "dispositivo", "medicion_nivel", "estado_puerta", "fecha")
    list_filter = ("estado_puerta", "fecha")
    search_fields = ("dispositivo__device_name",)
    inlines = [AlertaInline]
    actions = [generar_backup, eliminar_backup]

# =========================
# Admin Alerta
# =========================
@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ("id", "reporte", "mensaje", "is_activa", "fecha_alerta", "fecha_desactivada")
    list_filter = ("fecha_alerta",)
    search_fields = ("mensaje", "reporte__dispositivo__device_name")
