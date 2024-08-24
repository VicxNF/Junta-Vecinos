from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login
from .models import Vecino, ProyectoVecinal
from .forms import *

def index(request):
    return render(request, 'junta_vecinos/index.html')

def lista_vecinos(request):
    vecinos = Vecino.objects.all()
    return render(request, 'junta_vecinos/lista_vecinos.html', {'vecinos': vecinos})

def lista_proyectos(request):
    proyectos = ProyectoVecinal.objects.all()
    return render(request, 'junta_vecinos/lista_proyectos.html', {'proyectos': proyectos})

def crear_proyecto(request):
    if request.method == 'POST':
        form = ProyectoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_proyectos')
    else:
        form = ProyectoForm()
    return render(request, 'junta_vecinos/crear_proyecto.html', {'form': form})

def registro_vecino(request):
    if request.method == 'POST':
        form = RegistroVecinoForm(request.POST)
        if form.is_valid():
            vecino = form.save()
            login(request, vecino.user)  # Iniciar sesión automáticamente después del registro
            return redirect('lista_vecinos')  # Redirigir a la lista de vecinos después del registro
    else:
        form = RegistroVecinoForm()

    return render(request, 'junta_vecinos/registro.html', {'form': form})