from django.db import migrations, transaction
from django.contrib.auth.hashers import make_password

def create_initial_superuser(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    username = 'Kameid'
    email    = 'matias.kameid.v@gmail.com'
    password = '#KameidVL5'  # cámbiala a algo seguro

    if not User.objects.filter(username=username).exists():
        with transaction.atomic():
            User.objects.create(
                username=username,
                email=email,
                password=make_password(password),
                is_staff=True,
                is_superuser=True,
                is_active=True,
            )

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_alter_application_url'),
    ]


    operations = [
        migrations.RunPython(create_initial_superuser,
                            reverse_code=migrations.RunPython.noop),
    ]
