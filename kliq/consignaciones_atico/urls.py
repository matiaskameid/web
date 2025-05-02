# consignaciones_atico/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='consignaciones_atico_home'),
]
