from django.shortcuts import render

def index(request):
    # Por ahora un placeholder
    return render(request, 'consignaciones_atico/index.html')
