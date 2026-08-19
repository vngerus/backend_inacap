from django.shortcuts import render
from .models import Gato

def lista_gatos(request):
    gatos = Gato.objects.all()
    
    return render(request, 'registro/lista.html', {'gatos': gatos})