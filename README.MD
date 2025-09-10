# App Monitoreo de Contenedores IoT

![Python](https://img.shields.io/badge/python-3.11-blue)
![Django](https://img.shields.io/badge/django-4.x-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

## Descripción

Esta aplicación web permite monitorear contenedores IoT mostrando niveles de contenido, estado de puertas y alertas activas. Incluye funcionalidades de generación de reportes en PDF y una interfaz responsiva con soporte dark mode.

El sistema está diseñado para:

* Visualizar el estado de múltiples contenedores.
* Recibir alertas cuando los niveles superan un umbral crítico.
* Integrar un endpoint REST para recibir datos de módulos IoT (ESP32) que alimentan la información de los contenedores.
* Generar reportes filtrados según dispositivo, fecha y tipo de alerta.
* Gestionar usuarios con login y logout.

> **Nota:** Los datos no se muestran en tiempo real, sino que se actualizan periódicamente desde los módulos IoT.

## Tecnologías

* **Backend:** Django, Python
* **Frontend:** HTML, Tailwind CSS, HTMX, Alpine.js
* **Base de datos:** PostgreSQL
* **Otros:** Soporte para generación de PDFs, integración de endpoints REST para IoT

## Estructura de la aplicación

```
/app
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── dashboard_partial.html
│   ├── contenedor.html
│   ├── contenedor_partial.html
│   ├── report.html
│   └── report_partial.html
├── static/
├── views.py
├── models.py
├── urls.py
└── ...
```

## Funcionalidades principales

1. **Dashboard**

   * Visualización de contenedores con nivel de llenado y estado de puerta.
   * Alertas visuales y sonoras cuando el nivel supera el umbral crítico (≥ 75%).
   * Actualización periódica de información mediante HTMX.

2. **Detalle de Contenedor**

   * Visualización de nivel y estado de puerta.
   * Historial de alertas con activas y desactivadas.
   * Actualización automática cada pocos segundos desde el servidor.

3. **Reportes**

   * Búsqueda avanzada filtrando por dispositivo, fecha, hora y estado de alerta.
   * Paginación de resultados mediante HTMX.
   * Generación de PDF con los filtros aplicados.

4. **Usuarios**

   * Login y logout seguro.
   * Interfaz adaptativa para desktop y móvil.

5. **Integración IoT**

   * Endpoint REST que recibe información de múltiples módulos ESP32.
   * Almacena niveles de contenedor y estados de puerta para su posterior visualización y generación de reportes.

## Requisitos

* Python 3.11+
* Django 4.x
* PostgreSQL 13+
* Tailwind CSS
* HTMX
* Alpine.js

## Instalación rápida

```bash
git clone https://github.com/WolfWerkDev/App_Monitoreo_Contenedores.git
cd app-monitoreo-iot
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Acceder a la app en: `http://127.0.0.1:8000/`

## Licencia

Este proyecto está bajo la licencia **MIT License**. Consulte el archivo `LICENSE` para más detalles.
