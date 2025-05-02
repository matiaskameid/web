from django.apps import AppConfig
from django.apps import AppConfig
from django.conf import settings

class CoreConfig(AppConfig):
    name = 'core'
    verbose_name = "Core"

    def ready(self):
        # Esto se ejecuta al iniciar Django
        from django.contrib.auth import get_user_model
        from django.contrib.auth.hashers import make_password

        User = get_user_model()
        username = 'Kameid'
        email    = 'matias.kameid.v@gmail.com'
        password = '#KameidVL5'  # tu contraseña segura

        # Sólo lo creamos si no existe
        if not User.objects.filter(username=username).exists():
            print("Creando superusuario admin…")  # verás este mensaje en los logs
            User.objects.create(
                username=username,
                email=email,
                password=make_password(password),
                is_staff=True,
                is_superuser=True,
                is_active=True,
            )

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
