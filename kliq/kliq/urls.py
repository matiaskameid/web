from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from core.views import register

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', register, name='register'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('login/',    auth_views.LoginView.as_view(template_name='registration/login.html'),  name='login'),
    path('logout/',   auth_views.LogoutView.as_view(next_page='login'),                   name='logout'),
    path('', include('core.urls')),
    path('consignaciones-atico/', include('consignaciones_atico.urls')),
]
