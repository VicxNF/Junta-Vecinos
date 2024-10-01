from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout 
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import *
from .forms import *
import uuid
from django.utils import timezone
from django.db import IntegrityError
from django.http import JsonResponse
from django.utils.dateparse import parse_time
import json
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
from django.core.files.base import ContentFile
from datetime import date
from django.core.files.base import ContentFile
import json
from datetime import datetime, timedelta
from django.db.models import Count



def bienvenida(request):
    if request.user.is_authenticated:
        return redirect('index')  # Redirige al index si ya está autenticado
    return render(request, 'junta_vecinos/bienvenida.html')

@login_required
def index(request):
    vecinos = []
    solicitudes = []
    postulaciones = []
    noticias = []
    espacios = []
    reservas = []

    if request.user.is_authenticated:
        if request.user.is_superuser:
            vecinos = Vecino.objects.all()[:5]  # Muestra solo los primeros 5 vecinos
            solicitudes = SolicitudCertificado.objects.all()[:5]  # Muestra solo las primeras 5 solicitudes
            postulaciones = ProyectoVecinal.objects.all()[:5]  # Vista reducida de postulaciones (primeros 5)
            espacios = Espacio.objects.all()[:5] 
            reservas = Reserva.objects.all()[:5] 

        # Todos los usuarios, incluidos vecinos, verán las noticias
        noticias = Noticia.objects.all().order_by('-fecha_publicacion')

    return render(request, 'junta_vecinos/index.html', {
        'vecinos': vecinos,
        'solicitudes': solicitudes,
        'postulaciones': postulaciones,
        'noticias': noticias,
        'espacios': espacios,
        'reservas': reservas
    })


def is_admin(user):
    return user.is_superuser  # Solo permite el acceso si el usuario es un superusuario (admin)

def generar_username_unico(base_username):
    username = base_username
    n = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{n}"
        n += 1
    return username

@user_passes_test(is_admin)
@login_required
def lista_vecinos(request):
    vecinos = Vecino.objects.all()
    return render(request, 'junta_vecinos/lista_vecinos.html', {'vecinos': vecinos})

def registro_vecino(request):
    if request.method == 'POST':
        form = RegistroVecinoForm(request.POST)
        if form.is_valid():
            try:
                # Generar un nombre de usuario único basado en el email
                email = form.cleaned_data['email']
                base_username = email.split('@')[0]
                username = generar_username_unico(base_username)

                # Crear el usuario
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=form.cleaned_data['password'],
                    first_name=form.cleaned_data['nombres'],
                    last_name=form.cleaned_data['apellidos']
                )
                user.is_active = False
                user.save()

                # Crear el vecino asociado al usuario
                vecino = Vecino.objects.create(
                    user=user,
                    nombres=form.cleaned_data['nombres'],
                    apellidos=form.cleaned_data['apellidos'],
                    direccion=form.cleaned_data['direccion'],
                    telefono=form.cleaned_data['telefono'],
                    fecha_nacimiento=form.cleaned_data['fecha_nacimiento']
                )

                # Crear la solicitud de registro
                SolicitudRegistroVecino.objects.create(vecino=vecino)
                
                messages.success(request, 'Su solicitud de registro ha sido enviada y está pendiente de aprobación.')
                return redirect('login')
            except IntegrityError as e:
                messages.error(request, 'Ha ocurrido un error durante el registro. Por favor, inténtelo de nuevo.')
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
                    if user.is_active:
                        auth_login(request, user)
                        messages.success(request, f"¡Bienvenido {user.get_full_name()}!")
                        return redirect('index')
                    else:
                        messages.error(request, "Su cuenta aún no ha sido aprobada.")
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
def solicitudes_registro(request):
    if not request.user.is_staff:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('index')
    solicitudes = SolicitudRegistroVecino.objects.filter(is_approved=False)
    return render(request, 'junta_vecinos/solicitudes_registro.html', {'solicitudes': solicitudes})

@login_required
def aprobar_registro(request, solicitud_id):
    if not request.user.is_staff:
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('index')
    
    solicitud = get_object_or_404(SolicitudRegistroVecino, id=solicitud_id)
    vecino = solicitud.vecino
    user = vecino.user
    user.is_active = True
    user.save()
    
    solicitud.is_approved = True
    solicitud.save()

    # Enviar correo al vecino
    email = EmailMessage(
        subject='Solicitud de Registro Aprobada',
        body=f'Hola {vecino.nombres},\n\nNos complace informarte que tu solicitud de registro ha sido aprobada. Ya puedes ingresar al sistema.\n\nSaludos!',
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email.send()

    messages.success(request, f'La solicitud de {vecino.nombres} {vecino.apellidos} ha sido aprobada y se le ha enviado un correo.')
    return redirect('solicitudes_registro')

@login_required
def rechazar_registro(request, solicitud_id):
    if not request.user.is_staff:
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('index')

    solicitud = get_object_or_404(SolicitudRegistroVecino, id=solicitud_id)
    vecino = solicitud.vecino
    user = vecino.user

    if request.method == 'POST':
        form = RechazoCertificadoForm(request.POST)
        if form.is_valid():
            mensaje_rechazo = form.cleaned_data['mensaje_rechazo']
            
            # Eliminar al usuario y sus datos
            user.delete()
            vecino.delete()
            solicitud.delete()

            # Enviar correo al vecino con las razones del rechazo
            send_mail(
                'Solicitud de Registro Rechazada',
                f'Hola {vecino.nombres} {vecino.apellidos},\n\n'
                f'Lamentamos informarte que tu solicitud de registro ha sido rechazada por las siguientes razones:\n\n{mensaje_rechazo}\n\n'
                f'Si tienes dudas, por favor contacta con la administración.',
                settings.DEFAULT_FROM_EMAIL,
                [user.email]
            )

            messages.error(request, 'La solicitud ha sido rechazada y se ha enviado un correo al vecino.')
            return redirect('solicitudes_registro')
    else:
        form = RechazoCertificadoForm()

    return render(request, 'junta_vecinos/rechazar_registro.html', {'solicitud': solicitud, 'form': form})


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
    solicitudes = SolicitudCertificado.objects.all()
    return render(request, 'junta_vecinos/gestionar_solicitudes.html', {'solicitudes': solicitudes})

@user_passes_test(is_admin)
def ver_solicitud(request, id):
    solicitud = get_object_or_404(SolicitudCertificado, id=id)
    return render(request, 'junta_vecinos/ver_solicitud.html', {'solicitud': solicitud})

@user_passes_test(is_admin)
def aprobar_solicitud(request, id):
    solicitud = get_object_or_404(SolicitudCertificado, id=id)
    
    if request.method == 'POST':
        # Generar un número único de certificado
        numero_certificado = f"CERT-{solicitud.vecino.id}-{solicitud.id}"

        # Generar el PDF del certificado
        pdf_file = generar_certificado_pdf(solicitud.vecino, numero_certificado)

        # Guardar el certificado como un archivo
        certificado = CertificadoResidencia.objects.create(
            vecino=solicitud.vecino,
            numero_certificado=numero_certificado,
            documento_certificado=ContentFile(pdf_file, f"certificado_{numero_certificado}.pdf")
        )

        # Actualizar el estado de la solicitud
        solicitud.estado = 'Aprobado'
        solicitud.save()

        # Enviar el correo con el PDF adjunto
        email = EmailMessage(
            subject='Certificado de Residencia Aprobado',
            body=f'Hola {solicitud.vecino.nombres},\n\nEs de nuestro agrado informarle que su solicitud de certificado de residencia fue aprobado\n\nAdjunto encontrarás tu certificado de residencia.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[solicitud.vecino.user.email],
        )

        # Adjuntar el PDF al correo
        email.attach(f"certificado_{numero_certificado}.pdf", pdf_file, 'application/pdf')

        # Enviar el correo
        email.send()

        messages.success(request, 'La solicitud ha sido aprobada y el certificado generado.')
        return redirect('gestionar_solicitudes')

    return render(request, 'junta_vecinos/aprobar_solicitud.html', {'solicitud': solicitud})


@user_passes_test(is_admin)
def rechazar_solicitud(request, id):
    solicitud = get_object_or_404(SolicitudCertificado, id=id)

    if request.method == 'POST':
        form = RechazoCertificadoForm(request.POST)
        if form.is_valid():
            mensaje_rechazo = form.cleaned_data['mensaje_rechazo']

            # Actualizar el estado de la solicitud
            solicitud.estado = 'Rechazado'
            solicitud.save()

            # Enviar el correo al vecino con las razones del rechazo
            send_mail(
                'Solicitud de Certificado de Residencia Rechazada',
                f'Hola {solicitud.vecino.user.get_full_name()},\n\n'
                f'Tu solicitud ha sido rechazada por las siguientes razones:\n\n{mensaje_rechazo}\n\n'
                f'Si tienes dudas, por favor contacta con la administración.',
                settings.DEFAULT_FROM_EMAIL,
                [solicitud.vecino.user.email]
            )

            messages.error(request, 'La solicitud ha sido rechazada y se ha enviado un correo al vecino.')
            return redirect('gestionar_solicitudes')
    else:
        form = RechazoCertificadoForm()

    return render(request, 'junta_vecinos/rechazar_solicitud.html', {'solicitud': solicitud, 'form': form})


@user_passes_test(is_admin)
def enviar_certificado(request, id):
    solicitud = get_object_or_404(SolicitudCertificado, id=id)

    if request.method == 'POST':
        form = EnviarCertificadoForm(request.POST, request.FILES)
        if form.is_valid():
            # Guardar el documento del certificado
            certificado = CertificadoResidencia.objects.create(
                vecino=solicitud.vecino,
                numero_certificado=f"CERT-{solicitud.vecino.id}-{solicitud.id}",
                documento_certificado=form.cleaned_data['documento_certificado']
            )
            
            # Enviar el correo
            send_mail(
                'Certificado de Residencia Aprobado',
                form.cleaned_data['contenido_correo'] + f'\n\nPuedes descargar el certificado desde el siguiente enlace:\n\n{settings.SITE_URL}/media/{certificado.documento_certificado}',
                settings.DEFAULT_FROM_EMAIL,
                [solicitud.vecino.user.email],
                fail_silently=False,
            )

            # Actualizar el estado de la solicitud
            solicitud.estado = 'Aprobado'
            solicitud.save()

            messages.success(request, 'El certificado ha sido enviado y la solicitud ha sido aprobada.')
            return redirect('gestionar_solicitudes')
    else:
        form = EnviarCertificadoForm()

    return render(request, 'junta_vecinos/enviar_certificado.html', {'form': form, 'solicitud': solicitud})

@login_required
def postular_proyecto(request):
    try:
        vecino = request.user.vecino
    except Vecino.DoesNotExist:
        messages.error(request, 'No tienes un perfil de vecino asociado. Por favor, contacta con el administrador.')
        return redirect('index')

    if request.method == 'POST':
        form = ProyectoVecinalForm(request.POST, request.FILES)
        if form.is_valid():
            proyecto = form.save(commit=False)
            proyecto.vecino = vecino
            proyecto.save()
            messages.success(request, 'Tu proyecto ha sido postulado exitosamente.')
            return redirect('index')
    else:
        form = ProyectoVecinalForm()

    return render(request, 'junta_vecinos/postular_proyecto.html', {'form': form})


@user_passes_test(is_admin)
def gestionar_proyectos(request):
    proyectos = ProyectoVecinal.objects.filter(estado='pendiente')
    return render(request, 'junta_vecinos/gestionar_proyectos.html', {'proyectos': proyectos})

@user_passes_test(is_admin)
def ver_proyecto(request, id):
    proyecto = get_object_or_404(ProyectoVecinal, id=id)
    return render(request, 'junta_vecinos/ver_proyecto.html', {'proyecto': proyecto})

@user_passes_test(is_admin)
def aprobar_proyecto(request, id):
    proyecto = get_object_or_404(ProyectoVecinal, id=id)
    
    if request.method == 'POST':
        form = CorreoAprobacionForm(request.POST)
        if form.is_valid():
            # Cambiar estado y guardar
            proyecto.estado = 'aprobado'
            proyecto.save()
            
            # Enviar correo
            send_mail(
                'Proyecto Vecinal Aprobado',
                form.cleaned_data['contenido'],
                settings.DEFAULT_FROM_EMAIL,
                [proyecto.vecino.user.email]
            )
            messages.success(request, 'El proyecto ha sido aprobado y se ha enviado un correo al vecino.')
            return redirect('gestionar_proyectos')
    else:
        form = CorreoAprobacionForm()

    return render(request, 'junta_vecinos/aprobar_proyecto.html', {'form': form, 'proyecto': proyecto})

@user_passes_test(is_admin)
def rechazar_proyecto(request, id):
    proyecto = get_object_or_404(ProyectoVecinal, id=id)
    
    if request.method == 'POST':
        form = CorreoRechazoForm(request.POST)
        if form.is_valid():
            # Cambiar estado y guardar
            proyecto.estado = 'rechazado'
            proyecto.save()
            
            # Enviar correo
            send_mail(
                'Proyecto Vecinal Rechazado',
                form.cleaned_data['contenido'],
                settings.DEFAULT_FROM_EMAIL,
                [proyecto.vecino.user.email]
            )
            messages.success(request, 'El proyecto ha sido rechazado y se ha enviado un correo al vecino.')
            return redirect('gestionar_proyectos')
    else:
        form = CorreoRechazoForm()

    return render(request, 'junta_vecinos/rechazar_proyecto.html', {'form': form, 'proyecto': proyecto})

@user_passes_test(is_admin)
def publicar_noticia(request):
    if request.method == 'POST':
        form = NoticiaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = NoticiaForm()
    return render(request, 'junta_vecinos/publicar_noticia.html', {'form': form})


@user_passes_test(is_admin)
def gestionar_noticias(request):
    noticias = Noticia.objects.all().order_by('-fecha_publicacion')
    return render(request, 'junta_vecinos/gestionar_noticias.html', {'noticias': noticias})

@user_passes_test(is_admin)
def editar_noticia(request, id):
    noticia = get_object_or_404(Noticia, id=id)
    if request.method == 'POST':
        form = NoticiaForm(request.POST, request.FILES, instance=noticia)
        if form.is_valid():
            form.save()
            return redirect('gestionar_noticias')
    else:
        form = NoticiaForm(instance=noticia)
    return render(request, 'junta_vecinos/editar_noticia.html', {'form': form, 'noticia': noticia})


@user_passes_test(is_admin)
def registrar_espacio(request):
    if request.method == 'POST':
        form = EspacioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_espacios')  # Redirige a una página de éxito o lista de espacios
    else:
        form = EspacioForm()
    
    return render(request, 'junta_vecinos/registrar_espacio.html', {'form': form})

@user_passes_test(is_admin)
def lista_espacios(request):
    espacios = Espacio.objects.all()  # Obtén todos los espacios
    return render(request, 'junta_vecinos/lista_espacios.html', {'espacios': espacios})

@user_passes_test(is_admin)
def editar_espacio(request, espacio_id):
    espacio = get_object_or_404(Espacio, id=espacio_id)
    
    if request.method == 'POST':
        form = EspacioForm(request.POST, instance=espacio)
        if form.is_valid():
            form.save()
            return redirect('lista_espacios')  # Redirige a la lista de espacios
    else:
        form = EspacioForm(instance=espacio)
    
    return render(request, 'junta_vecinos/editar_espacio.html', {'form': form, 'espacio': espacio})

@user_passes_test(is_admin)
def eliminar_espacio(request, espacio_id):
    espacio = get_object_or_404(Espacio, id=espacio_id)
    if request.method == 'POST':
        espacio.delete()
        return redirect('lista_espacios')  # Redirige a la lista después de eliminar
    return redirect('lista_espacios')  # Por si acceden a la URL por GET

@login_required
def espacios_disponibles(request):
    espacios = Espacio.objects.all()
    return render(request, 'junta_vecinos/espacios_disponibles.html', {'espacios': espacios})

@login_required
def reservar_espacio(request, espacio_id):
    espacio = get_object_or_404(Espacio, id=espacio_id)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            fecha = data.get('fecha')
            hora_inicio = data.get('hora_inicio')
            hora_fin = data.get('hora_fin')

            # Verificar si ya existe una reserva para ese espacio, fecha y horas
            reservas_existentes = Reserva.objects.filter(
                espacio=espacio,
                fecha=fecha,
                hora_inicio__lt=hora_fin,
                hora_fin__gt=hora_inicio
            )
            if reservas_existentes.exists():
                return JsonResponse({'success': False, 'error': 'El espacio ya está reservado en ese horario.'})

            # Crear la reserva
            reserva = Reserva.objects.create(
                usuario=request.user,
                espacio=espacio,
                fecha=fecha,
                hora_inicio=hora_inicio,
                hora_fin=hora_fin
            )
            return JsonResponse({'success': True})
        
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@login_required
def get_available_slots(request):
    date = request.GET.get('date')
    espacio_id = request.GET.get('espacio_id')
    espacio = get_object_or_404(Espacio, id=espacio_id)

    # Definir horarios disponibles (ajusta según tus necesidades)
    start_time = datetime.strptime('08:00', '%H:%M').time()
    end_time = datetime.strptime('22:00', '%H:%M').time()
    slot_duration = timedelta(minutes=30)

    # Obtener todas las reservas para ese día y espacio
    reservas = Reserva.objects.filter(espacio=espacio, fecha=date)

    all_slots = []
    current_time = start_time
    while current_time < end_time:
        slot_end = (datetime.combine(datetime.min, current_time) + slot_duration).time()
        if slot_end > end_time:
            slot_end = end_time

        is_available = not reservas.filter(
            hora_inicio__lt=slot_end,
            hora_fin__gt=current_time
        ).exists()

        all_slots.append({
            'start': current_time.strftime('%H:%M'),
            'end': slot_end.strftime('%H:%M'),
            'available': is_available
        })

        current_time = slot_end

    return JsonResponse({'slots': all_slots})

@user_passes_test(is_admin)
@login_required
def lista_reservas(request):
    # Obtener todas las reservas
    reservas = Reserva.objects.all()

    # Agrupar las reservas por espacio y contar cuántas hay por espacio
    reservas_por_espacio = Reserva.objects.values('espacio__nombre').annotate(total=Count('id')).order_by('espacio__nombre')

    # Obtener nombres de los espacios y totales
    espacios = [reserva['espacio__nombre'] for reserva in reservas_por_espacio]
    totales = [reserva['total'] for reserva in reservas_por_espacio]

    return render(request, 'junta_vecinos/lista_reservas.html', {
        'reservas': reservas,
        'espacios': espacios,
        'totales': totales
    })


def generar_certificado_pdf(vecino, numero_certificado):
    # Renderizar el contenido HTML con los datos del vecino
    html_content = render_to_string('junta_vecinos/certificado_residencia.html', {
        'vecino': vecino,
        'numero_certificado': numero_certificado,
        'fecha_emision': date.today().strftime('%d/%m/%Y'),
    })

    # Generar el PDF usando WeasyPrint
    pdf_file = HTML(string=html_content).write_pdf()

    return pdf_file