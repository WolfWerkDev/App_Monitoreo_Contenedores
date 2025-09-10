from django import forms  # Importa el módulo de formularios de Django

# Formulario para iniciar sesión de usuarios
class UserLogin(forms.Form):
    # Campo de correo electrónico
    email = forms.CharField(
        label="Correo electrónico",  # Etiqueta que se muestra en el formulario
        max_length=100,  # Longitud máxima del correo
        widget=forms.EmailInput(attrs={  # Define el tipo de input HTML y sus atributos
            "class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            # Clases CSS de Tailwind para estilo del input
        })
    )

    # Campo de contraseña
    password = forms.CharField(
        label="Contraseña",  # Etiqueta que se muestra en el formulario
        max_length=20,  # Longitud máxima de la contraseña
        widget=forms.PasswordInput(attrs={  # Input de tipo password para ocultar caracteres
            "class": "shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            # Clases CSS de Tailwind para estilo del input
        })
    )
