from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout 
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import *
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

def registro_vecino(request):
    if request.method == 'POST':
        form = RegistroVecinoForm(request.POST)
        if form.is_valid():
            vecino = form.save()
            auth_login(request, vecino.user)  # Iniciar sesión automáticamente después del registro
            messages.success(request, 'Registro exitoso. Has iniciado sesión automáticamente.')
            return redirect('index')
    else:
        form = RegistroVecinoForm()
    return render(request, 'junta_vecinos/registro.html', {'form': form})

def user_login(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                user = User.objects.get(email=email)
                user = authenticate(request, username=user.username, password=password)
                if user is not None:
                    auth_login(request, user)
                    messages.success(request, f"¡Bienvenido {user.get_full_name()}!")
                    return redirect('index')
                else:
                    messages.error(request, "Correo electrónico o contraseña incorrectos.")
            except User.DoesNotExist:
                messages.error(request, "El correo electrónico no está registrado.")
    else:
        form = LoginForm()
    
    return render(request, 'junta_vecinos/login.html', {'form': form})


def user_logout(request):
    logout(request)
    messages.success(request, "Has cerrado sesión exitosamente.")
    return redirect('login')

@login_required
def solicitar_certificado(request):
    try:
        vecino = request.user.vecino
    except Vecino.DoesNotExist:
        messages.error(request, 'No tienes un perfil de vecino asociado. Por favor, contacta con el administrador.')
        return redirect('index')

    if request.method == 'POST':
        form = SolicitudCertificadoForm(request.POST, request.FILES)
        if form.is_valid():
            solicitud = form.save(commit=False)
            solicitud.vecino = vecino
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
    
    if request.method == 'POST':
        form = DocumentoCertificadoForm(request.POST, request.FILES)
        if form.is_valid():
            # Guardar el documento del certificado
            certificado = CertificadoResidencia.objects.create(
                vecino=solicitud.vecino,
                numero_certificado=f"CERT-{solicitud.vecino.id}-{solicitud.id}",
                documento_certificado=form.cleaned_data['documento_certificado']
            )
            # Actualizar el estado de la solicitud
            solicitud.estado = 'aprobado'
            solicitud.save()

            # Enviar un correo al vecino
            send_mail(
                'Certificado de Residencia Aprobado',
                f'Hola {solicitud.vecino.user.get_full_name()},\n\nTu solicitud de certificado de residencia ha sido aprobada. Puedes descargar el certificado desde el siguiente enlace:\n\n{settings.SITE_URL}/media/{certificado.documento_certificado}',
                settings.DEFAULT_FROM_EMAIL,
                [solicitud.vecino.user.email]
            )

            messages.success(request, 'La solicitud ha sido aprobada y el certificado generado. Se ha enviado un correo al vecino.')
            return redirect('gestionar_solicitudes')
    else:
        form = DocumentoCertificadoForm()

    return render(request, 'junta_vecinos/aprobar_solicitud.html', {'solicitud': solicitud, 'form': form})


@user_passes_test(is_admin)
def rechazar_solicitud(request, id):
    solicitud = get_object_or_404(SolicitudCertificado, id=id)
    solicitud.estado = 'rechazado'
    solicitud.save()
    messages.error(request, 'La solicitud ha sido rechazada.')
    return redirect('gestionar_solicitudes')