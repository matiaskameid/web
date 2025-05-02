# WEB/kliq/consignaciones_atico/urls.py
from django.urls import path
from . import views

app_name = 'consignaciones_atico'

urlpatterns = [
    path('', views.index, name='index'),
]
