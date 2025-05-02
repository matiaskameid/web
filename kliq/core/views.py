# WEB/kliq/core/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth import get_user_model

def home(request):
    """
    Página principal: renderiza templates/home.html
    """
    return render(request, 'home.html')

def register(request):
    """
    Formulario de registro: renderiza registration/register.html
    """
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f'Usuario "{user.username}" creado correctamente. ¡Ya puedes iniciar sesión!'
            )
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def debug_users(request):
    """
    Devuelve un JSON con todos los usuarios y sus flags de staff/superuser.
    SOLO para debugging; retíralo después.
    """
    User = get_user_model()
    users = list(
        User.objects.values("username", "is_staff", "is_superuser")
    )
    return JsonResponse(users, safe=False)