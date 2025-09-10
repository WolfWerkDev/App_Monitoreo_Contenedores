from django.shortcuts import render, get_object_or_404  # Funciones para renderizar templates y obtener objetos
from dashboard.models import Dispositivo, Reporte, Alerta  # Importa modelos del dashboard
from django.contrib.auth.decorators import login_required  # Protege vistas con login

# Vista para mostrar detalle de un contenedor específico
@login_required
def detalle_contenedor(request, id):
    # Obtiene el dispositivo o lanza 404 si no existe
    dispositivo = get_object_or_404(Dispositivo, id=id)

    # Último reporte asociado al dispositivo
    reporte = Reporte.objects.filter(dispositivo=dispositivo).order_by("-fecha").first()

    # Construir datos adicionales para usar en el template
    dispositivo.ultimo_nivel = reporte.medicion_nivel if reporte else 0
    dispositivo.ultima_fecha = reporte.fecha if reporte else None
    dispositivo.estado_actual_puerta = reporte.estado_puerta if reporte else None

    # Última alerta activa del dispositivo
    ultima_alerta = Alerta.objects.filter(
        reporte__dispositivo=dispositivo,
        is_activa=True
    ).order_by("-fecha_alerta").first()

    # Renderiza el template con la información del dispositivo y última alerta activa
    return render(request, "contenedor/contenedor.html", {
        "dispositivo": dispositivo,
        "ultima_alerta": ultima_alerta
    })

# Vista parcial para actualizar información del contenedor (por ejemplo, vía AJAX)
@login_required
def contenedor_partial(request, device_id):
    dispositivo = get_object_or_404(Dispositivo, id=device_id)

    # Último reporte asociado
    reporte = Reporte.objects.filter(dispositivo=dispositivo).order_by("-fecha").first()

    # Construir datos adicionales
    dispositivo.ultimo_nivel = reporte.medicion_nivel if reporte else 0
    dispositivo.ultima_fecha = reporte.fecha if reporte else None
    dispositivo.estado_actual_puerta = reporte.estado_puerta if reporte else None

    # Obtener la última alerta activa
    ultima_alerta = Alerta.objects.filter(
        reporte__dispositivo=dispositivo,
        is_activa=True
    ).order_by("-fecha_alerta").first()

    # Renderiza un template parcial con la información actualizada
    return render(request, "contenedor/contenedor_partial.html", {
        "dispositivo": dispositivo,
        "ultima_alerta": ultima_alerta
    })

# Vista para manejar alertas de un dispositivo específico
@login_required
def alertas(request, device_id):
    dispositivo = get_object_or_404(Dispositivo, id=device_id)

    # Obtener todos los reportes de ese dispositivo
    reportes_dispositivo = Reporte.objects.filter(dispositivo=dispositivo)

    # Buscar la última alerta activa asociada a cualquiera de esos reportes
    ultima_alerta = Alerta.objects.filter(
        reporte__in=reportes_dispositivo,
        is_activa=True
    ).order_by("-fecha_alerta").first()

    # Renderiza el template parcial con la información de la alerta
    return render(request, "contenedor/contenedor_partial.html", {
        "dispositivo": dispositivo,
        "ultima_alerta": ultima_alerta
    })
