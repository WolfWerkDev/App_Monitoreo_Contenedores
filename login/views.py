from django.shortcuts import render, redirect  # Funciones para renderizar templates y redirigir URLs
from django.contrib.auth import authenticate, login as auth_login  # Funciones de autenticación de Django
from .forms import UserLogin  # Importa el formulario de login personalizado

# Vista para el login de usuarios
def login(request):
    # Si el usuario envía el formulario (POST)
    if request.method == 'POST':
        form = UserLogin(request.POST)  # Crea una instancia del formulario con los datos enviados
        if form.is_valid():  # Valida los datos del formulario
            email = form.cleaned_data["email"]  # Obtiene el email limpio
            password = form.cleaned_data["password"]  # Obtiene la contraseña limpia

            # Autenticación del usuario usando email y contraseña
            user = authenticate(request, email=email, password=password)
            if user is not None:  # Si la autenticación es correcta
                auth_login(request, user)  # Inicia la sesión del usuario
                return redirect("/dashboard/")  # Redirige al dashboard después del login
            else:
                # Si la autenticación falla, vuelve a mostrar el formulario con mensaje de error
                return render(request, "registration/login.html", {
                    "form": form,
                    "error": "Usuario o contraseña incorrectos"
                })
    else:
        # Si es una petición GET, se muestra un formulario vacío
        form = UserLogin()

    # Renderiza el template de login con el formulario (vacío o con errores)
    return render(request, "registration/login.html", {"form": form})


def home(request):
    # Redirige siempre al login
    return redirect('/login/')