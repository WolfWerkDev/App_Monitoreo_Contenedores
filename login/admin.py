from django.contrib import admin  # Importa el módulo de administración de Django
from django.contrib.auth.admin import UserAdmin  # Importa UserAdmin para extender el admin de usuarios
from .models import Usuario  # Importa el modelo Usuario definido en models.py del mismo directorio

# Registra el modelo Usuario en el panel de administración de Django
@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    # Campos básicos que se mostrarán en la lista de usuarios del admin
    base_fields = ["email", "name", "is_staff", "is_superuser"]
    
    # Campos personalizados adicionales a mostrar en el admin con etiquetas amigables
    custom_display_fields = {
        "ID_Card": "Número documento",  # Muestra el número de documento con nombre legible
        # se pueden agregar más campos personalizados aquí
        # "otro_campo": "Etiqueta bonita"
    }

    # Combina los campos básicos y los personalizados para mostrar en la lista
    list_display = base_fields + list(custom_display_fields.keys())

    # Campos por los que se puede buscar en el panel de administración
    search_fields = ("email", "name", "ID_Card")

    # Define cómo se agrupan los campos al editar un usuario existente
    fieldsets = (
        (None, {"fields": ("email", "password")}),  # Credenciales principales
        ("Información personal", {"fields": ("name", "ID_Card")}),  # Información del usuario
        ("Permisos", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),  # Permisos y grupos
    )

    # Campos que aparecen al crear un nuevo usuario desde el admin
    add_fieldsets = (
        (None, {
            "classes": ("wide",),  # Clase CSS para estilo ancho en el admin
            "fields": ("email", "name", "ID_Card", "password1", "password2"),  # Campos obligatorios para creación
        }),
    )

    # Orden predeterminado de los usuarios en la lista (por email)
    ordering = ("email",)

    # Mejora la selección de grupos y permisos con un widget horizontal
    filter_horizontal = ("groups", "user_permissions")

    # Método especial para manejar campos personalizados que no existen directamente en UserAdmin
    def __getattr__(self, name):
        if name in self.custom_display_fields:
            # Retorna el valor del campo personalizado para mostrar en list_display
            def _func(obj):
                return getattr(obj, name)  # Obtiene el valor real del objeto
            _func.short_description = self.custom_display_fields[name]  # Nombre legible en el admin
            return _func
        # Si el atributo no existe, lanza un error estándar
        raise AttributeError(f"{self.__class__.__name__} object has no attribute {name}")
