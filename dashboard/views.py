from django.shortcuts import render, redirect  # Funciones para renderizar templates y redirigir
from .models import Dispositivo, Reporte, Alerta  # Importa los modelos del dashboard
from django.db.models import OuterRef, Subquery  # Para consultas avanzadas tipo subquery
from django.http import JsonResponse  # Para responder con JSON
import json  # Para decodificar JSON recibido
from django.utils import timezone  # Para obtener fecha y hora actual
from django.views.decorators.csrf import csrf_exempt  # Para eximir CSRF en endpoints externos
from django.contrib.auth import logout  # Para cerrar sesión
from django.contrib.auth.decorators import login_required  # Para proteger vistas con login
from django.views.decorators.cache import never_cache  # Para evitar cache de la vista
from datetime import timedelta, date

hoy = date.today()


@login_required
@never_cache
def dashboard(request):
    dispositivos = Dispositivo.objects.annotate(
        ultimo_nivel=Subquery(
            Reporte.objects.filter(dispositivo=OuterRef("pk"))
            .order_by("-fecha")
            .values("medicion_nivel")[:1]
        ),
        ultima_fecha=Subquery(
            Reporte.objects.filter(dispositivo=OuterRef("pk"))
            .order_by("-fecha")
            .values("fecha")[:1]
        ),
        estado_actual_puerta=Subquery(
            Reporte.objects.filter(dispositivo=OuterRef("pk"))
            .order_by("-fecha")
            .values("estado_puerta")[:1]
        ),
    )

    hoy = now().date()
    for d in dispositivos:
        alertas_cerradas = Alerta.objects.filter(
            reporte__dispositivo=d, is_activa=False, fecha_desactivada__isnull=False
        )
        # --- Promedio total ---
        tiempos = [(a.fecha_desactivada - a.fecha_alerta).total_seconds()/60 for a in alertas_cerradas]
        if tiempos:
            total_seconds = int((sum(tiempos)/len(tiempos)) * 60)
            d.tiempo_atencion = str(timedelta(seconds=total_seconds))
        else:
            d.tiempo_atencion = None

        # --- Promedio diario ---
        alertas_hoy = alertas_cerradas.filter(fecha_alerta__date=hoy)
        tiempos_hoy = [(a.fecha_desactivada - a.fecha_alerta).total_seconds()/60 for a in alertas_hoy]
        if tiempos_hoy:
            total_seconds_hoy = int((sum(tiempos_hoy)/len(tiempos_hoy)) * 60)
            d.tiempo_atencion_dia = str(timedelta(seconds=total_seconds_hoy))
        else:
            d.tiempo_atencion_dia = None

    return render(request, "dashboard/dashboard.html", {"dispositivos": dispositivos})

@login_required
def dashboard_partial(request):
    dispositivos = Dispositivo.objects.annotate(
        ultimo_nivel=Subquery(
            Reporte.objects.filter(dispositivo=OuterRef("pk"))
            .order_by("-fecha")
            .values("medicion_nivel")[:1]
        ),
        ultima_fecha=Subquery(
            Reporte.objects.filter(dispositivo=OuterRef("pk"))
            .order_by("-fecha")
            .values("fecha")[:1]
        ),
        estado_actual_puerta=Subquery(
            Reporte.objects.filter(dispositivo=OuterRef("pk"))
            .order_by("-fecha")
            .values("estado_puerta")[:1]
        ),
    )

    for d in dispositivos:
        alertas_cerradas = Alerta.objects.filter(
            reporte__dispositivo=d, is_activa=False, fecha_desactivada__isnull=False
        )
        # --- Promedio total ---
        tiempos = [(a.fecha_desactivada - a.fecha_alerta).total_seconds()/60 for a in alertas_cerradas]
        if tiempos:
            total_seconds = int((sum(tiempos)/len(tiempos)) * 60)
            d.tiempo_atencion = str(timedelta(seconds=total_seconds))
        else:
            d.tiempo_atencion = None

        # --- Promedio diario ---
        alertas_hoy = alertas_cerradas.filter(fecha_alerta__date=hoy)
        tiempos_hoy = [(a.fecha_desactivada - a.fecha_alerta).total_seconds()/60 for a in alertas_hoy]
        if tiempos_hoy:
            total_seconds_hoy = int((sum(tiempos_hoy)/len(tiempos_hoy)) * 60)
            d.tiempo_atencion_dia = str(timedelta(seconds=total_seconds_hoy))
        else:
            d.tiempo_atencion_dia = None

    return render(request, "dashboard/dashboard.html", {"dispositivos": dispositivos})


# Endpoint para recibir información enviada desde el ESP32
@csrf_exempt  # Deshabilita CSRF para este endpoint
def reporte_ESP32(request):
    if request.method == "POST":
        data = request.body.decode('utf-8')  # Recibe JSON enviado por ESP32
        try: 
            info = json.loads(data)  # Decodifica JSON
            id_device = info.get('id_device')  # Obtiene id del dispositivo
            medida_nivel = info.get('nivel')  # Obtiene nivel medido
            estado_puerta = info.get('puerta')  # Obtiene estado de puerta

            # Validar que el dispositivo exista
            try:
                dispositivo = Dispositivo.objects.get(id=id_device)
            except Dispositivo.DoesNotExist:
                raise ValueError(f"El dispositivo con id {id_device} no existe")
            
            # Crear un nuevo reporte en la base de datos
            reporte = Reporte.objects.create(
                dispositivo=dispositivo,
                medicion_nivel=medida_nivel,
                estado_puerta=estado_puerta,
                fecha=timezone.now()
            )

            # Revisar si hay alerta activa para el dispositivo
            alerta_activa = Alerta.objects.filter(
                reporte__dispositivo=dispositivo,
                is_activa=True
            ).order_by("-fecha_alerta").first()

            # Crear alerta si el nivel supera 75 y no hay alerta activa
            if medida_nivel >= 75:
                if not alerta_activa:
                    mensaje_alerta = f"VACIAR CONTENEDOR - Nivel medido: {medida_nivel}%"
                    Alerta.objects.create(
                        reporte=reporte,
                        mensaje=mensaje_alerta,
                        fecha_alerta=timezone.now(),
                        is_activa=True
                    )
            else:
                # Si hay alerta activa y el nivel bajó, desactivarla
                if alerta_activa:
                    alerta_activa.is_activa = False
                    alerta_activa.fecha_desactivada = timezone.now()
                    alerta_activa.save()

            # Respuesta exitosa al ESP32
            return JsonResponse({"status": "ok", "reporte_id": reporte.id})

        except json.JSONDecodeError:
            # JSON inválido
            return JsonResponse({"status": "error", "message": "Datos JSON no válidos"})
        except ValueError as ve:
            # Error de validación de datos
            return JsonResponse({"status": "error", "message": str(ve)})

    else:
        # Método no permitido
        return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)
    
# Vista para cerrar sesión
def logout_view(request):
    logout(request)  # Cierra sesión del usuario
    request.session.flush()  # Limpia la sesión
    return redirect('/login/')  # Redirige al login

# Nueva función para calcular el promedio de tiempo de atención de alertas
from django.utils.timezone import now
from django.http import JsonResponse

@login_required
def promedio_tiempo_alertas(request):
    """
    Devuelve el promedio de tiempo de atención de alertas en dos versiones:
    - promedio_tiempo_alertas_min: promedio general acumulado.
    - promedio_tiempo_alertas_dia_min: promedio solo del día actual.
    """
    # --- Promedio general ---
    alertas_cerradas = (
        Alerta.objects.filter(is_activa=False, fecha_desactivada__isnull=False)
        .select_related("reporte__dispositivo")
    )

    tiempos_total = {}
    for alerta in alertas_cerradas:
        dispositivo_id = alerta.reporte.dispositivo.id
        t_min = (alerta.fecha_desactivada - alerta.fecha_alerta).total_seconds() / 60
        tiempos_total.setdefault(dispositivo_id, []).append(t_min)

    promedios_total = {
        d: round(sum(tiempos) / len(tiempos), 2)
        for d, tiempos in tiempos_total.items()
    }

    # --- Promedio solo del día actual ---
    hoy = now().date()
    alertas_hoy = alertas_cerradas.filter(fecha_alerta__date=hoy)

    tiempos_hoy = {}
    for alerta in alertas_hoy:
        dispositivo_id = alerta.reporte.dispositivo.id
        t_min = (alerta.fecha_desactivada - alerta.fecha_alerta).total_seconds() / 60
        tiempos_hoy.setdefault(dispositivo_id, []).append(t_min)

    promedios_hoy = {
        d: round(sum(tiempos) / len(tiempos), 2)
        for d, tiempos in tiempos_hoy.items()
    }

    return JsonResponse({
        "promedio_tiempo_alertas_min": promedios_total,
        "promedio_tiempo_alertas_dia_min": promedios_hoy,
    })
