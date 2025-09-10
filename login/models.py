from django.db import models  # Importa las herramientas de modelos de Django
from django.contrib.auth.models import AbstractUser, BaseUserManager  # Importa clases para usuario personalizado

# Manager personalizado para el modelo Usuario
class UsuarioManager(BaseUserManager):
    # Método para crear un usuario normal
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El usuario debe tener un correo electrónico")  # Verificación de email obligatorio
        email = self.normalize_email(email)  # Normaliza el email (minusculas, etc.)
        user = self.model(email=email, **extra_fields)  # Crea instancia del usuario
        user.set_password(password)  # Encripta la contraseña
        user.save(using=self._db)  # Guarda el usuario en la base de datos
        return user

    # Método para crear un superusuario
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)  # Superusuario siempre es staff
        extra_fields.setdefault("is_superuser", True)  # Superusuario siempre tiene permisos totales

        return self.create_user(email, password, **extra_fields)  # Reutiliza create_user

# Modelo de usuario personalizado
class Usuario(AbstractUser):
    username = None  # Se elimina el campo username predeterminado
    email = models.EmailField("email", unique=True)  # Se usa email como campo único y principal

    # Campos adicionales del usuario
    name = models.CharField(max_length=200)  # Nombre completo del usuario
    ID_Card = models.CharField(max_length=10, unique=True)  # Número de documento único

    # Configuración para autenticación
    USERNAME_FIELD = "email"  # Se autentica por email
    REQUIRED_FIELDS = ["name"]  # Campos obligatorios al crear superusuario

    # Asocia el manager personalizado al modelo
    objects = UsuarioManager()

    # Representación legible del usuario
    def __str__(self):
        return f"{self.name} ({self.email})" 
    
    # Propiedad para obtener solo el primer nombre
    @property
    def first_name_only(self):
        return self.name.split(" ")[0] if self.name else ""  # Retorna primer nombre o vacío si no hay
