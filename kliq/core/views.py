# WEB/kliq/core/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages

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
