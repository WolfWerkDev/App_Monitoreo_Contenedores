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

# Vista principal del dashboard, protegida por login y sin cache
@login_required
@never_cache
def dashboard(request):
    # Anota cada dispositivo con los últimos valores de nivel, fecha y estado de puerta
    dispositivos = Dispositivo.objects.annotate(
        ultimo_nivel=Subquery(
            Reporte.objects.filter(dispositivo=OuterRef("pk"))
            .order_by("-fecha")
            .values("medicion_nivel")[:1]  # Último nivel medido
        ),
        ultima_fecha=Subquery(
            Reporte.objects.filter(dispositivo=OuterRef("pk"))
            .order_by("-fecha")
            .values("fecha")[:1]  # Fecha del último reporte
        ),
        estado_puerta=Subquery(
            Reporte.objects.filter(dispositivo=OuterRef("pk"))
            .order_by("-fecha")
            .values("estado_puerta")[:1]  # Estado de puerta del último reporte
        ),
    )
    # Renderiza el template principal con los dispositivos anotados
    return render(request, "dashboard/dashboard.html", {"dispositivos": dispositivos})

# Vista parcial del dashboard para actualizaciones parciales (AJAX)
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
    )
    return render(request, "dashboard/dashboard_partial.html", {"dispositivos": dispositivos})

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
