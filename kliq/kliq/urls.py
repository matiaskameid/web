from django.contrib import admin
from django.urls import path, include
from core.views import home, register

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),

    # rutas de login/logout (django.contrib.auth)
    path('accounts/', include('django.contrib.auth.urls')),

    # ruta para registro de nuevo usuario
    path('accounts/register/', register, name='register'),
]
