from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = "Core"

    def ready(self):
        """
        Al iniciar Django, garantiza que exista un superusuario
        'Kameid' con contraseña '#KameidVL5', y lo fuerza si ya existe.
        """
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()

            username = 'Kameid'
            email    = 'matias.kameid.v@gmail.com'
            password = '#KameidVL5'

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'is_staff': True,
                    'is_superuser': True,
                    'is_active': True,
                }
            )

            # Si ya existía, forzamos que tenga la contraseña y flags correctos
            if not created:
                user.set_password(password)
                user.email = email
                user.is_staff = True
                user.is_superuser = True
                user.is_active = True
                user.save()
                print("🔑 Superusuario Kameid actualizado con contraseña forzada")
            else:
                # Si lo acabamos de crear, asignamos la contraseña
                user.set_password(password)
                user.save()
                print("🔑 Superusuario Kameid creado en arrancado")

        except Exception as e:
            # Si algo falla (por ejemplo, migraciones no aplicadas), lo ignoramos
            print(f"⚠️ Error en CoreConfig.ready(): {e}")
