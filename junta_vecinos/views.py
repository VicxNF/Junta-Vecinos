from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Vecino, ProyectoVecinal
from .forms import *

def bienvenida(request):
    if request.user.is_authenticated:
        return redirect('index')  # Redirige al index si ya está autenticado
    return render(request, 'junta_vecinos/bienvenida.html')

@login_required
def index(request):
    return render(request, 'junta_vecinos/index.html')

def is_admin(user):
    return user.is_superuser  # Solo permite el acceso si el usuario es un superusuario (admin)

@user_passes_test(is_admin)
@login_required
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

def user_login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f"¡Bienvenido {user.username}!")
            return redirect('index')  # Redirige a la página principal después del login
        else:
            messages.error(request, "Nombre de usuario o contraseña incorrectos.")
    
    return render(request, 'junta_vecinos/login.html')

def user_logout(request):
    logout(request)
    messages.success(request, "Has cerrado sesión exitosamente.")
    return redirect('login')

@login_required
def solicitar_certificado(request):
    if request.method == 'POST':
        form = SolicitudCertificadoForm(request.POST, request.FILES)
        if form.is_valid():
            solicitud = form.save(commit=False)
            solicitud.vecino = request.user.vecino  # Asocia la solicitud con el vecino logueado
            solicitud.save()
            messages.success(request, 'Tu solicitud de certificado de residencia ha sido enviada.')
            return redirect('index')
    else:
        form = SolicitudCertificadoForm()
    return render(request, 'junta_vecinos/solicitar_certificado.html', {'form': form})

@user_passes_test(is_admin)
def gestionar_solicitudes(request):
    solicitudes = SolicitudCertificado.objects.filter(estado='pendiente')
    return render(request, 'junta_vecinos/gestionar_solicitudes.html', {'solicitudes': solicitudes})

@user_passes_test(is_admin)
def ver_solicitud(request, id):
    solicitud = get_object_or_404(SolicitudCertificado, id=id)
    return render(request, 'junta_vecinos/ver_solicitud.html', {'solicitud': solicitud})

@user_passes_test(is_admin)
def aprobar_solicitud(request, id):
    solicitud = get_object_or_404(SolicitudCertificado, id=id)
    solicitud.estado = 'aprobado'
    solicitud.save()

    # Generar el certificado de residencia
    CertificadoResidencia.objects.create(
        vecino=solicitud.vecino,
        numero_certificado=f"CERT-{solicitud.vecino.id}-{solicitud.id}"
    )

    messages.success(request, 'La solicitud ha sido aprobada y el certificado generado.')
    return redirect('gestionar_solicitudes')

@user_passes_test(is_admin)
def rechazar_solicitud(request, id):
    solicitud = get_object_or_404(SolicitudCertificado, id=id)
    solicitud.estado = 'rechazado'
    solicitud.save()
    messages.error(request, 'La solicitud ha sido rechazada.')
    return redirect('gestionar_solicitudes')