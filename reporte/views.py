from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .forms import informe
from django.views.decorators.cache import never_cache
from django.http import HttpResponse, FileResponse
from dashboard.models import Dispositivo, Reporte, Alerta
from datetime import datetime
from django.utils import timezone
from django.core.paginator import Paginator
from reportlab.lib.pagesizes import A4 
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from io import BytesIO

# =========================================================
# VISTA PRINCIPAL DE REPORTES
# =========================================================
@login_required
@never_cache
def reporte(request):
    """
    Renderiza la página de reportes o el partial para HTMX/POST.
    Filtra por dispositivo, tipo de informe, alertas, fecha y hora.
    Maneja paginación de resultados.
    """
    reportes = []
    dispositivos = []
    is_htmx = request.headers.get("HX-Request") == "true" or request.META.get("HTTP_HX_REQUEST") == "true"

    # Procesar filtros si es POST o HTMX GET
    if request.method == 'POST' or (is_htmx and request.method == 'GET'):
        data = request.POST if request.method == 'POST' else request.GET
        form = informe(data)
        if form.is_valid():
            contenedor = form.cleaned_data["dispositivos"]
            tipo_informe = form.cleaned_data["tipo_informe"]
            estado_alerta = form.cleaned_data["estado_alerta"]
            de_fecha = form.cleaned_data["de_fecha"]
            fecha = form.cleaned_data["fecha"]
            de_hora = form.cleaned_data["de_hora"]
            hora_1 = form.cleaned_data["hora1"]
            hora_2 = form.cleaned_data["hora2"]

            dispositivo = obtener_dispositivo(contenedor)
            if dispositivo == "all":
                if tipo_informe == "reporte":
                    reportes = get_all_reports(de_fecha, fecha, de_hora, hora_1, hora_2)
                elif tipo_informe == "alerta":
                    reportes = get_all_alerts(estado_alerta, de_fecha, fecha, de_hora, hora_1, hora_2)
                dispositivos = all_devices()
            elif dispositivo:
                reportes = obtener_informe_id(dispositivo, tipo_informe, estado_alerta, de_fecha, fecha, de_hora, hora_1, hora_2)
    else:
        form = informe()

    # Paginación de resultados
    page_number = request.GET.get("page", 1)
    paginator = Paginator(reportes, 10)
    page_obj = paginator.get_page(page_number)

    # Elegir template parcial o completo
    template = "report/report_partial.html" if (request.method == "POST" or is_htmx) else "report/report.html"

    return render(request, template, {
        "form": form,
        "reportes": page_obj,
        "dispositivos": dispositivos,
    })


# =========================================================
# FUNCIONES AUXILIARES PARA FILTRADO Y OBTENCIÓN DE DATOS
# =========================================================
def obtener_dispositivo(contenedor):
    """Devuelve el id del dispositivo o 'all' si se seleccionan todos"""
    if contenedor != "all":
        try:
            device = Dispositivo.objects.get(id=int(contenedor))
            return device.id
        except Dispositivo.DoesNotExist:
            return []
    else:
        return "all"

def obtener_nombre_device(contenedor):
    """Obtiene el nombre del dispositivo por su id"""
    try:
        device = Dispositivo.objects.get(id=int(contenedor))
        return device.device_name
    except Dispositivo.DoesNotExist:
        return "Desconocido"

def obtener_reporte(device_id, caso):
    """Obtiene todos los reportes de un dispositivo"""
    if caso == "all":
        return list(Reporte.objects.filter(dispositivo=device_id).order_by('-fecha'))

def obtener_alerta(lista_reportes, caso, estado_alerta):
    """Filtra los reportes según el estado de las alertas"""
    if caso == "all":
        if estado_alerta == "todas":
            return [r for r in lista_reportes if r.alertas.exists()]
        elif estado_alerta == "activas":
            return [r for r in lista_reportes if r.alertas.filter(is_activa=True).exists()]
        elif estado_alerta == "inactivas":
            return [r for r in lista_reportes if r.alertas.filter(is_activa=False).exists()]

def filtrar_por_hora(lista_reportes, fecha, de_hora, hora1=None, hora2=None):
    """Filtra reportes según hora dentro de una fecha específica"""
    if de_hora == "antes" and hora1:
        filtro_dt = timezone.make_aware(datetime.combine(fecha, hora1))
        return [r for r in lista_reportes if r.fecha < filtro_dt]
    if de_hora == "entre" and hora1 and hora2:
        filtro_dt1 = timezone.make_aware(datetime.combine(fecha, hora1))
        filtro_dt2 = timezone.make_aware(datetime.combine(fecha, hora2))
        return [r for r in lista_reportes if filtro_dt1 < r.fecha < filtro_dt2]
    if de_hora == "despues" and hora1:
        filtro_dt = timezone.make_aware(datetime.combine(fecha, hora1))
        return [r for r in lista_reportes if r.fecha > filtro_dt]
    return lista_reportes

def obtener_informe_id(device_id, tipo_informe, estado_alerta, de_fecha, fecha, de_hora, hora1, hora2):
    """Genera el informe filtrado para un solo dispositivo"""
    if tipo_informe == "reporte" and not any([de_fecha, fecha, de_hora, hora1, hora2]):
        return obtener_reporte(device_id, caso="all")
    if tipo_informe == "alerta" and not any([de_fecha, fecha, de_hora, hora1, hora2]):
        lista_reportes = obtener_reporte(device_id, caso="all")
        return obtener_alerta(lista_reportes, caso="all", estado_alerta=estado_alerta)

    # Filtrado por fecha
    if tipo_informe == "reporte":
        if de_fecha:
            if de_fecha == "antes":
                return list(Reporte.objects.filter(dispositivo=device_id, fecha__lte=fecha).order_by("-fecha"))
            elif de_fecha == "en":
                lista_reportes = list(Reporte.objects.filter(dispositivo=device_id, fecha__date=fecha).order_by("-fecha"))
                if de_hora:
                    return filtrar_por_hora(lista_reportes, fecha, de_hora, hora1, hora2)
                return lista_reportes
            elif de_fecha == "despues":
                return list(Reporte.objects.filter(dispositivo=device_id, fecha__date__gt=fecha).order_by("-fecha"))
    elif tipo_informe == "alerta":
        lista_reportes = []
        if de_fecha == "antes":
            lista_reportes = list(Reporte.objects.filter(dispositivo=device_id, fecha__lte=fecha).order_by("-fecha"))
        elif de_fecha == "en":
            lista_reportes = list(Reporte.objects.filter(dispositivo=device_id, fecha__date=fecha).order_by("-fecha"))
            if de_hora:
                lista_reportes = filtrar_por_hora(lista_reportes, fecha, de_hora, hora1, hora2)
        elif de_fecha == "despues":
            lista_reportes = list(Reporte.objects.filter(dispositivo=device_id, fecha__date__gt=fecha).order_by("-fecha"))
        return obtener_alerta(lista_reportes, caso="all", estado_alerta=estado_alerta)

def all_devices():
    """Devuelve todos los dispositivos"""
    return list(Dispositivo.objects.all())

def get_all_reports(de_fecha=None, fecha=None, de_hora=None, hora1=None, hora2=None):
    """Obtiene todos los reportes, opcionalmente filtrados por fecha y hora"""
    lista_reportes = list(Reporte.objects.all().order_by("-fecha"))
    if de_fecha:
        if de_fecha == "antes" and fecha:
            lista_reportes = [r for r in lista_reportes if r.fecha.date() <= fecha]
        elif de_fecha == "en" and fecha:
            lista_reportes = [r for r in lista_reportes if r.fecha.date() == fecha]
            if de_hora:
                lista_reportes = filtrar_por_hora(lista_reportes, fecha, de_hora, hora1, hora2)
        elif de_fecha == "despues" and fecha:
            lista_reportes = [r for r in lista_reportes if r.fecha.date() > fecha]
    return lista_reportes

def get_all_alerts(estado_alerta="todas", de_fecha=None, fecha=None, de_hora=None, hora1=None, hora2=None):
    """Obtiene todos los reportes con alertas filtradas"""
    lista_reportes = get_all_reports(de_fecha, fecha, de_hora, hora1, hora2)
    return obtener_alerta(lista_reportes, caso="all", estado_alerta=estado_alerta)


# =========================================================
# GENERACIÓN DE PDF
# =========================================================
@login_required
def generar_pdf(request):
    """Genera un PDF con los reportes o alertas según filtros"""
    reportes = []
    form = informe(request.POST or None)
    if not form.is_valid():
        return HttpResponse("Formulario no válido o faltan datos.", status=400)

    contenedor = form.cleaned_data["dispositivos"]
    tipo_informe = form.cleaned_data["tipo_informe"]
    estado_alerta = form.cleaned_data["estado_alerta"]
    de_fecha = form.cleaned_data["de_fecha"]
    fecha = form.cleaned_data["fecha"]
    de_hora = form.cleaned_data["de_hora"]
    hora1 = form.cleaned_data["hora1"]
    hora2 = form.cleaned_data["hora2"]

    dispositivo = obtener_dispositivo(contenedor)

    if tipo_informe == "reporte":
        campo_principal = "Reporte"
        tipo_titulo = "Reportes"
    elif tipo_informe == "alerta":
        campo_principal = "Alerta"
        tipo_titulo = "Alertas"
    else:
        campo_principal = "Campo"
        tipo_titulo = "Información"

    if dispositivo == "all":
        reportes_existentes = (
            get_all_reports(de_fecha, fecha, de_hora, hora1, hora2)
            if tipo_informe == "reporte"
            else get_all_alerts(estado_alerta, de_fecha, fecha, de_hora, hora1, hora2)
        ) or []  # <-- corrección mínima
        dispositivos = all_devices()
        todos_reportes = []
        for d in dispositivos:
            r_dispositivo = [r for r in reportes_existentes if r.dispositivo == d]
            if r_dispositivo:
                todos_reportes.extend(r_dispositivo)
            else:
                class TempR:
                    dispositivo = d
                    medicion_nivel = 0
                    estado_puerta = False
                    fecha = "N/A"
                    alertas = []
                todos_reportes.append(TempR())
        reportes = todos_reportes
        nombre_titulo = f"Informe-{tipo_titulo}-General"
    else:
        nombre_device = obtener_nombre_device(contenedor)
        reportes = obtener_informe_id(dispositivo, tipo_informe, estado_alerta, de_fecha, fecha, de_hora, hora1, hora2)
        nombre_titulo = f"Informe-{tipo_titulo}-{nombre_device}"

    # Variables para totales
    suma_nivel = 0
    count_nivel = 0
    apertura_puerta = 0
    duracion_alertas = []
    alertas_activas = False

    # Crear PDF
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50

    # Título principal
    pdf.setFont("Helvetica-Bold", 20)
    pdf.setFillColor(colors.darkblue)
    pdf.drawCentredString(width / 2, y, nombre_titulo)
    y -= 30

    # Descripción
    total_resultados = len(reportes)
    pdf.setFont("Helvetica", 11)
    pdf.setFillColor(colors.black)
    lineas_descripcion = [
        f"Este informe contiene información de {tipo_titulo.lower()}.",
        f"Total de resultados: {total_resultados}.",
        f"Informe generado el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
    ]
    for linea in lineas_descripcion:
        pdf.drawCentredString(width / 2, y, linea)
        y -= 15
    y -= 20

    if not reportes:
        pdf.setFont("Helvetica", 12)
        pdf.drawString(50, y, "No se encontraron registros para los filtros seleccionados.")
    else:
        for idx, r in enumerate(reportes, start=1):
            device_name = getattr(r.dispositivo, 'device_name', str(r.dispositivo))
            nivel = getattr(r, 'medicion_nivel', 0)
            if isinstance(nivel, (int, float)):
                suma_nivel += nivel
                count_nivel += 1
            if not getattr(r, 'estado_puerta', False):
                apertura_puerta += 1

            fecha_local = timezone.localtime(getattr(r, 'fecha'))

            data = [
                [f"{idx}. {campo_principal}", "Valor"],
                ["Dispositivo", device_name],
                ["Medición Nivel", f"{nivel}%"],
                ["Estado Puerta", "Cerrada" if getattr(r, 'estado_puerta', False) else "Abierta"],
                ["Fecha", fecha_local.strftime("%Y-%m-%d %H:%M:%S")]
            ]

            if hasattr(r, 'alertas') and getattr(r.alertas, 'exists', lambda: False)():
                for a in r.alertas.all():
                    fecha_off = timezone.localtime(getattr(a, 'fecha_desactivada'))
                    fecha_local = timezone.localtime(getattr(a, 'fecha_alerta'))
                    estado = "Activa" if getattr(a, 'is_activa', False) else "Desactivada"

                    fecha_alerta_str = fecha_local.strftime('%Y-%m-%d %H:%M:%S')
                    fecha_off_str = fecha_off.strftime('%Y-%m-%d %H:%M:%S') if getattr(a, 'is_activa') else "N/A"

                    mensaje = f"{getattr(a, 'mensaje', '')} - {fecha_alerta_str} - Fecha desactivación: {fecha_off_str}"
                    data.append([f"Alerta ({estado})", mensaje])

                    if estado == "Activa":
                        alertas_activas = True

                    fecha_inicio = getattr(a, 'fecha_alerta', None)
                    fecha_fin = getattr(a, 'fecha_desactivada', None)
                    if fecha_inicio and fecha_fin:
                        duracion_alertas.append((fecha_fin - fecha_inicio).total_seconds())


            col_widths = [100, width - 200]
            table = Table(data, colWidths=col_widths)
            style = TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                ('TEXTCOLOR',(0,0),(-1,0),colors.black),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 10),
                ('BOX', (0,0), (-1,-1), 0.5, colors.grey),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('ALIGN', (0,0), (0,-1), 'RIGHT'),
            ])
            for i in range(1, len(data)):
                bg_color = colors.whitesmoke if i % 2 == 0 else colors.lightcyan
                style.add('BACKGROUND', (0,i), (-1,i), bg_color)
                if "Alerta" in str(data[i][0]):
                    if "Activa" in data[i][0]:
                        style.add('BACKGROUND', (0,i), (-1,i), colors.red)
                        style.add('TEXTCOLOR', (0,i), (-1,i), colors.white)
                    else:
                        style.add('BACKGROUND', (0,i), (-1,i), colors.yellow)
                        style.add('TEXTCOLOR', (0,i), (-1,i), colors.black)
            table.setStyle(style)
            w, h = table.wrap(0, 0)
            if y - h < 50:
                pdf.showPage()
                y = height - 50
            table.drawOn(pdf, 50, y - h)
            y -= h + 20

        if tipo_informe == "alerta" and not alertas_activas:
            pdf.setFont("Helvetica-Bold", 12)
            pdf.setFillColor(colors.red)
            pdf.drawString(50, y, "No hay alertas activas en este momento.")
            y -= 20

        # Totales generales
        pdf.setFont("Helvetica-Bold", 12)
        pdf.setFillColor(colors.darkblue)
        y -= 20
        pdf.drawString(50, y, "Totales Generales:")
        y -= 15

        promedio_nivel = suma_nivel / count_nivel if count_nivel > 0 else 0
        promedio_alertas_min = (sum(duracion_alertas)/len(duracion_alertas)/60) if duracion_alertas else 0

        pdf.setFont("Helvetica", 11)
        pdf.setFillColor(colors.black)
        pdf.drawString(60, y, f"Promedio de nivel medido: {promedio_nivel:.2f}%")
        y -= 15
        pdf.drawString(60, y, f"Cantidad de veces que se abrió la puerta: {apertura_puerta}")
        y -= 15
        pdf.drawString(60, y, f"Duración promedio de alertas: {promedio_alertas_min:.2f} minutos")
        y -= 15

        if tipo_informe == "reporte":
            total_alertas = sum([len(r.alertas.all()) if hasattr(r, 'alertas') and getattr(r.alertas, 'exists', lambda: False)() else 0 for r in reportes])
            pdf.drawString(60, y, f"Cantidad total de alertas registradas: {total_alertas}")
            y -= 15

    pdf.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"{nombre_titulo}.pdf")
