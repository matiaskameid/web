from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from .forms import RegisterForm

def register(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method=='POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"¡Bienvenido, {user.username}!")
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def home(request):
    apps = [
        { 'name': 'Consignaciones Atico',
          'url':  'consignaciones_atico:index' },
    ]
    return render(request, 'core/home.html', {'apps': apps})