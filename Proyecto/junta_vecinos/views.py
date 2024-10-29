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
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponse
from django.utils.dateparse import parse_time
import json
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
from django.core.files.base import ContentFile
from datetime import datetime, date
from django.core.files.base import ContentFile
import json
from datetime import datetime, timedelta
from django.db.models import Count
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.shortcuts import redirect
from django.urls import reverse
from transbank.webpay.webpay_plus.transaction import Transaction
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal




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
    comuna = ""

    if request.user.is_authenticated:
        if request.user.is_superuser:
            admin = AdministradorComuna.objects.get(user=request.user)
            comuna = admin.get_comuna_display()
            
            vecinos = Vecino.objects.filter(administrador=admin)[:5]
            solicitudes = SolicitudCertificado.objects.filter(vecino__administrador=admin)[:5]
            postulaciones = ProyectoVecinal.objects.filter(vecino__administrador=admin)[:5]
            espacios = Espacio.objects.filter(comuna=admin)[:5]
            reservas = Reserva.objects.filter(espacio__comuna=admin)[:5]
            noticias = Noticia.objects.filter(comuna=admin).order_by('-fecha_publicacion')[:5]
        else:
            try:
                vecino = Vecino.objects.get(user=request.user)
                comuna = vecino.get_comuna_display()
                noticias = Noticia.objects.filter(comuna__comuna=vecino.comuna).order_by('-fecha_publicacion')[:5]
            except Vecino.DoesNotExist:
                noticias = []

    return render(request, 'junta_vecinos/index.html', {
        'vecinos': vecinos,
        'solicitudes': solicitudes,
        'postulaciones': postulaciones,
        'noticias': noticias,
        'espacios': espacios,
        'reservas': reservas,
        'comuna': comuna
    })


def is_admin(user):
    return hasattr(user, 'administradorcomuna')  # Solo permite el acceso si el usuario es un superusuario (admin)

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
    admin = request.user.administradorcomuna
    vecinos = Vecino.objects.filter(comuna=admin.comuna)
    return render(request, 'junta_vecinos/lista_vecinos.html', {'vecinos': vecinos})

def registro_vecino(request):
    if request.method == 'POST':
        form = RegistroVecinoForm(request.POST)
        if form.is_valid():
            vecino = form.save()
            messages.success(request, 'Su solicitud de registro ha sido enviada y está pendiente de aprobación.')
            return redirect('login')
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
    if not hasattr(request.user, 'administradorcomuna'):
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('index')
    
    admin = request.user.administradorcomuna
    solicitudes = SolicitudRegistroVecino.objects.filter(
        vecino__comuna=admin.comuna,
        is_approved=False
    )
    return render(request, 'junta_vecinos/solicitudes_registro.html', {'solicitudes': solicitudes})

@login_required
def aprobar_registro(request, solicitud_id):
    if not hasattr(request.user, 'administradorcomuna'):
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('index')
    
    solicitud = get_object_or_404(SolicitudRegistroVecino, id=solicitud_id)
    
    # Verificar que el administrador pertenece a la misma comuna que el vecino
    if solicitud.vecino.comuna != request.user.administradorcomuna.comuna:
        messages.error(request, 'No tienes permiso para aprobar esta solicitud.')
        return redirect('solicitudes_registro')
    
    vecino = solicitud.vecino
    user = vecino.user
    user.is_active = True
    user.save()
    
    solicitud.is_approved = True
    solicitud.save()

    send_mail(
        'Solicitud de Registro Aprobada',
        f'Hola {vecino.nombres},\n\nNos complace informarte que tu solicitud de registro ha sido aprobada. Ya puedes ingresar al sistema.\n\nSaludos!',
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
    )

    messages.success(request, f'La solicitud de {vecino.nombres} {vecino.apellidos} ha sido aprobada y se le ha enviado un correo.')
    return redirect('solicitudes_registro')

@login_required
def rechazar_registro(request, solicitud_id):
    if not hasattr(request.user, 'administradorcomuna'):
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('index')

    solicitud = get_object_or_404(SolicitudRegistroVecino, id=solicitud_id)
    
    # Verificar que el administrador pertenece a la misma comuna que el vecino
    if solicitud.vecino.comuna != request.user.administradorcomuna.comuna:
        messages.error(request, 'No tienes permiso para rechazar esta solicitud.')
        return redirect('solicitudes_registro')

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
    
    # Contar las solicitudes aprobadas y rechazadas
    aprobadas = solicitudes.filter(estado='Aprobado').count()
    rechazadas = solicitudes.filter(estado='Rechazado').count()
    
    return render(request, 'junta_vecinos/gestionar_solicitudes.html', {
        'solicitudes': solicitudes,
        'aprobadas': aprobadas,
        'rechazadas': rechazadas
    })

@user_passes_test(is_admin)
@login_required
def generar_reporte_solicitudes_pdf(request):
    # Crear el objeto HttpResponse con el tipo de contenido PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_solicitudes.pdf"'

    # Crear el PDF
    p = canvas.Canvas(response, pagesize=A4)
    ancho, alto = A4

    # Título
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, alto - 50, "Reporte de Solicitudes de Certificados")

    # Encabezados de la tabla
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, alto - 100, "Vecino")
    p.drawString(200, alto - 100, "Fecha de Solicitud")
    p.drawString(350, alto - 100, "Estado")

    # Listar las solicitudes
    p.setFont("Helvetica", 10)
    y = alto - 120
    solicitudes = SolicitudCertificado.objects.all().order_by('fecha_solicitud')
    for solicitud in solicitudes:
        if y < 50:
            p.showPage()  # Crear nueva página si se acaba el espacio
            y = alto - 50

        p.drawString(50, y, f"{solicitud.vecino.nombres} {solicitud.vecino.apellidos}")
        p.drawString(200, y, solicitud.fecha_solicitud.strftime("%Y-%m-%d"))
        p.drawString(350, y, solicitud.get_estado_display())
        y -= 20

    # Finalizar el PDF
    p.showPage()
    p.save()
    
    return response

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
def crear_proyecto(request):
    try:
        vecino = request.user.vecino
    except Vecino.DoesNotExist:
        messages.error(request, "Debes estar registrado como vecino para crear proyectos.")
        return redirect('index')

    if request.method == 'POST':
        form = ProyectoVecinalForm(request.POST, request.FILES)
        if form.is_valid():
            proyecto = form.save(commit=False)
            proyecto.vecino = vecino
            proyecto.save()
            
            # Enviar correo al administrador
            admin_email = vecino.administrador.user.email
            send_mail(
                'Nuevo Proyecto Vecinal',
                f'Se ha recibido un nuevo proyecto vecinal: {proyecto.propuesta}',
                settings.DEFAULT_FROM_EMAIL,
                [admin_email],
                fail_silently=True,
            )
            
            messages.success(request, "Tu proyecto ha sido enviado para revisión.")
            return redirect('mis_proyectos')
    else:
        form = ProyectoVecinalForm()
    
    return render(request, 'junta_vecinos/crear_proyecto.html', {'form': form})

@login_required
def mis_proyectos(request):
    try:
        vecino = request.user.vecino
        proyectos = ProyectoVecinal.objects.filter(vecino=vecino)
        return render(request, 'junta_vecinos/mis_proyectos.html', {'proyectos': proyectos})
    except Vecino.DoesNotExist:
        messages.error(request, "Debes estar registrado como vecino para ver proyectos.")
        return redirect('index')

@login_required
def detalle_proyecto(request, proyecto_id):
    proyecto = get_object_or_404(ProyectoVecinal, id=proyecto_id)
    if request.user != proyecto.vecino.user and not hasattr(request.user, 'administradorcomuna'):
        messages.error(request, "No tienes permiso para ver este proyecto.")
        return redirect('index')
    return render(request, 'junta_vecinos/detalle_proyecto.html', {'proyecto': proyecto})

# Vista para el administrador
@login_required
def admin_proyectos(request):
    if not hasattr(request.user, 'administradorcomuna'):
        messages.error(request, "No tienes permiso para acceder a esta página.")
        return redirect('index')
    
    admin = request.user.administradorcomuna
    proyectos = ProyectoVecinal.objects.filter(vecino__comuna=admin.comuna)
    return render(request, 'junta_vecinos/admin_proyectos.html', {'proyectos': proyectos})

@login_required
def evaluar_proyecto(request, proyecto_id):
    if not hasattr(request.user, 'administradorcomuna'):
        messages.error(request, "No tienes permiso para realizar esta acción.")
        return redirect('index')
    
    proyecto = get_object_or_404(ProyectoVecinal, id=proyecto_id)
    
    if request.method == 'POST':
        estado = request.POST.get('estado')
        razon_rechazo = request.POST.get('razon_rechazo')
        
        proyecto.estado = estado
        if estado == 'rechazado':
            proyecto.razon_rechazo = razon_rechazo
        proyecto.save()
        
        # Enviar correo al vecino
        send_mail(
            'Actualización de tu Proyecto Vecinal',
            f'Tu proyecto "{proyecto.propuesta}" ha sido {estado}.' + 
            (f'\nRazón del rechazo: {razon_rechazo}' if estado == 'rechazado' else ''),
            settings.DEFAULT_FROM_EMAIL,
            [proyecto.vecino.user.email],
            fail_silently=True,
        )
        
        messages.success(request, f"El proyecto ha sido {estado}.")
        return redirect('admin_proyectos')
    
    return render(request, 'junta_vecinos/evaluar_proyecto.html', {'proyecto': proyecto})

@login_required
def proyectos_comuna(request):
    try:
        vecino = request.user.vecino
        proyectos = ProyectoVecinal.objects.filter(
            vecino__comuna=vecino.comuna,
            estado='aprobado'
        ).exclude(vecino=vecino)
        
        # Obtener las postulaciones del vecino actual
        postulaciones = {
            p.proyecto_id: p.estado 
            for p in PostulacionProyecto.objects.filter(vecino=vecino)
        }
        
        for proyecto in proyectos:
            proyecto.estado_postulacion = postulaciones.get(proyecto.id)
        
        return render(request, 'junta_vecinos/proyectos_comuna.html', {
            'proyectos': proyectos
        })
    except Vecino.DoesNotExist:
        messages.error(request, "Debes estar registrado como vecino para ver los proyectos.")
        return redirect('index')
    
@login_required
def postular_proyecto(request, proyecto_id):
    try:
        vecino = request.user.vecino
        proyecto = get_object_or_404(ProyectoVecinal, id=proyecto_id, estado='aprobado')
        
        # Verificar que el vecino sea de la misma comuna
        if vecino.comuna != proyecto.vecino.comuna:
            messages.error(request, "Solo puedes postular a proyectos de tu comuna.")
            return redirect('proyectos_comuna')
        
        # Verificar que no sea el creador del proyecto
        if proyecto.vecino == vecino:
            messages.error(request, "No puedes postular a tu propio proyecto.")
            return redirect('proyectos_comuna')
        
        # Verificar si ya existe una postulación
        if PostulacionProyecto.objects.filter(proyecto=proyecto, vecino=vecino).exists():
            messages.error(request, "Ya te has postulado a este proyecto.")
            return redirect('proyectos_comuna')
        
        if request.method == 'POST':
            form = PostulacionProyectoForm(request.POST)
            if form.is_valid():
                postulacion = form.save(commit=False)
                postulacion.proyecto = proyecto
                postulacion.vecino = vecino
                postulacion.save()
                
                # Enviar correo al creador del proyecto
                send_mail(
                    'Nueva postulación a tu proyecto',
                    f'El vecino {vecino.nombres} {vecino.apellidos} se ha postulado a tu proyecto "{proyecto.propuesta}".',
                    None,
                    [proyecto.vecino.user.email],
                    fail_silently=True,
                )
                
                messages.success(request, "Tu postulación ha sido enviada correctamente.")
                return redirect('proyectos_comuna')
        else:
            form = PostulacionProyectoForm()
        
        return render(request, 'junta_vecinos/postular_proyecto.html', {
            'form': form,
            'proyecto': proyecto
        })
        
    except Vecino.DoesNotExist:
        messages.error(request, "Debes estar registrado como vecino para postular.")
        return redirect('index')

@login_required
def gestionar_postulaciones(request, proyecto_id):
    proyecto = get_object_or_404(ProyectoVecinal, id=proyecto_id)
    
    # Verificar que el usuario sea el creador del proyecto
    if request.user != proyecto.vecino.user:
        messages.error(request, "No tienes permiso para gestionar las postulaciones de este proyecto.")
        return redirect('mis_proyectos')
    
    if request.method == 'POST':
        postulacion_id = request.POST.get('postulacion_id')
        accion = request.POST.get('accion')
        
        postulacion = get_object_or_404(PostulacionProyecto, id=postulacion_id, proyecto=proyecto)
        
        if accion in ['aceptada', 'rechazada']:
            postulacion.estado = accion
            postulacion.fecha_respuesta = timezone.now()
            postulacion.save()
            
            # Enviar correo al postulante
            estado_esp = 'aceptada' if accion == 'aceptada' else 'rechazada'
            send_mail(
                f'Tu postulación ha sido {estado_esp}',
                f'Tu postulación al proyecto "{proyecto.propuesta}" ha sido {estado_esp}.',
                None,
                [postulacion.vecino.user.email],
                fail_silently=True,
            )
            
            messages.success(request, f"La postulación ha sido {estado_esp}.")
        
    postulaciones = proyecto.postulaciones.all().order_by('-fecha_postulacion')
    return render(request, 'junta_vecinos/gestionar_postulaciones.html', {
        'proyecto': proyecto,
        'postulaciones': postulaciones
    })

@user_passes_test(is_admin)
def publicar_noticia(request):
    if request.method == 'POST':
        form = NoticiaForm(request.POST, request.FILES)
        if form.is_valid():
            noticia = form.save(commit=False)
            admin = AdministradorComuna.objects.get(user=request.user)
            noticia.comuna = admin
            noticia.save()
            return redirect('index')
    else:
        form = NoticiaForm()
    return render(request, 'junta_vecinos/publicar_noticia.html', {'form': form})


@user_passes_test(is_admin)
def gestionar_noticias(request):
    admin = AdministradorComuna.objects.get(user=request.user)  # Obtener el administrador actual
    noticias = Noticia.objects.filter(comuna=admin).order_by('-fecha_publicacion')  # Filtrar noticias por administrador
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

@login_required
def detalle_noticia(request, noticia_id):
    # Obtener la noticia o devolver 404 si no existe
    noticia = get_object_or_404(Noticia, id=noticia_id)
    
    # Obtener la comuna desde el contexto o configuración
    try:
        from django.conf import settings
        comuna = settings.COMUNA_NOMBRE
    except:
        comuna = "Comuna"

    # Contexto para la plantilla
    context = {
        'noticia': noticia,
        'comuna': comuna
    }
    
    return render(request, 'junta_vecinos/detalle_noticia.html', context)


@user_passes_test(is_admin)
def registrar_espacio(request):
    if request.method == 'POST':
        form = EspacioForm(request.POST, request.FILES)
        if form.is_valid():
            espacio = form.save(commit=False)
            admin = AdministradorComuna.objects.get(user=request.user)
            espacio.comuna = admin
            espacio.save()
            return redirect('lista_espacios')  # Redirige a una página de éxito o lista de espacios
    else:
        form = EspacioForm()
    
    admin = AdministradorComuna.objects.get(user=request.user)
    context = {
        'form': form,
        'comuna': admin.get_comuna_display()
    }
    return render(request, 'junta_vecinos/registrar_espacio.html', context)

@user_passes_test(is_admin)
def lista_espacios(request):
    # Obtener la comuna del administrador autenticado
    administrador = AdministradorComuna.objects.get(user=request.user)
    
    # Filtrar los espacios según la comuna del administrador
    espacios = Espacio.objects.filter(comuna=administrador)
    
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
    # Obtener el vecino asociado al usuario actual
    vecino = get_object_or_404(Vecino, user=request.user)
    
    # Filtrar los espacios según la comuna del vecino
    espacios = Espacio.objects.filter(comuna__comuna=vecino.comuna)
    
    espacio_seleccionado = None
    if request.method == 'GET' and 'espacio_id' in request.GET:
        espacio_id = request.GET.get('espacio_id')
        # Asegurarse de que el espacio seleccionado también pertenece a la comuna del vecino
        espacio_seleccionado = get_object_or_404(Espacio, id=espacio_id, comuna__comuna=vecino.comuna)
    
    return render(request, 'junta_vecinos/espacios_disponibles.html', {
        'espacios': espacios,
        'espacio_seleccionado': espacio_seleccionado
    })



@login_required
def get_espacio_info(request):
    espacio_id = request.GET.get('espacio_id')
    espacio = get_object_or_404(Espacio, id=espacio_id)
    return JsonResponse({
        'nombre': espacio.nombre,
        'ubicacion': espacio.ubicacion,
        'foto': espacio.foto.url if espacio.foto else '',
    })

@login_required
def reservar_espacio(request, espacio_id):
    espacio = get_object_or_404(Espacio, id=espacio_id)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            fecha = data.get('fecha')
            hora_inicio = data.get('hora_inicio')
            hora_fin = data.get('hora_fin')

            # Convertir las horas a objetos time
            hora_inicio_obj = datetime.strptime(hora_inicio, '%H:%M').time()
            hora_fin_obj = datetime.strptime(hora_fin, '%H:%M').time()

            # Verificar si ya existe una reserva para ese espacio, fecha y horas
            reservas_existentes = Reserva.objects.filter(
                espacio=espacio,
                fecha=fecha,
                hora_inicio__lt=hora_fin_obj,
                hora_fin__gt=hora_inicio_obj
            )
            if reservas_existentes.exists():
                return JsonResponse({'success': False, 'error': 'El espacio ya está reservado en parte o todo ese horario.'})

            # Calcular el monto a pagar (esto dependerá de tu lógica de negocio)
            monto = calcular_monto(espacio, hora_inicio_obj, hora_fin_obj)

            # Iniciar transacción WebPay
            buy_order = f"RES-{espacio.id}-{request.user.id}-{int(datetime.now().timestamp())}"
            session_id = request.session.session_key
            return_url = request.build_absolute_uri(reverse('webpay_retorno'))

            transaction = Transaction()
            response = transaction.create(buy_order, session_id, monto, return_url)

            # Guardar datos de la reserva en sesión para procesarla después del pago
            request.session['reserva_pendiente'] = {
                'espacio_id': espacio.id,
                'fecha': fecha,
                'hora_inicio': hora_inicio,
                'hora_fin': hora_fin,
                'monto': monto,
                'buy_order': buy_order
            }

            # Devolver la URL de pago y el token para que el frontend redirija
            return JsonResponse({
                'success': True,
                'payment_url': response['url'],
                'token': response['token']
            })
        
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Método no permitido'})

def calcular_monto(espacio, hora_inicio, hora_fin):
    # Calcular la duración en horas
    duracion = datetime.combine(datetime.min, hora_fin) - datetime.combine(datetime.min, hora_inicio)
    horas = Decimal(duracion.total_seconds()) / Decimal(3600)  # Convertimos a Decimal

    # Multiplicar el precio por hora (Decimal) con las horas (Decimal)
    return int(espacio.precio_por_hora * horas)

@csrf_exempt
def webpay_retorno(request):
    if request.method == 'POST' or request.method == 'GET':
        token = request.POST.get('token_ws') if request.method == 'POST' else request.GET.get('token_ws')
        
        if not token:
            return render(request, 'junta_vecinos/error_reserva.html', {'error': 'Token de pago no recibido'})
        
        transaction = Transaction()
        response = transaction.commit(token)

        if response['response_code'] == 0:
            # Pago exitoso
            reserva_data = request.session.get('reserva_pendiente')
            if reserva_data and reserva_data['buy_order'] == response['buy_order']:
                # Crear la reserva
                espacio = get_object_or_404(Espacio, id=reserva_data['espacio_id'])
                reserva = Reserva.objects.create(
                    usuario=request.user,
                    espacio=espacio,
                    fecha=reserva_data['fecha'],
                    hora_inicio=datetime.strptime(reserva_data['hora_inicio'], '%H:%M').time(),
                    hora_fin=datetime.strptime(reserva_data['hora_fin'], '%H:%M').time(),
                    monto_pagado=response['amount']
                )
                del request.session['reserva_pendiente']
                return render(request, 'junta_vecinos/reserva_exitosa.html', {'reserva': reserva})
            else:
                return render(request, 'junta_vecinos/error_reserva.html', {'error': 'Datos de reserva no coinciden'})
        else:
            # Pago fallido
            return render(request, 'junta_vecinos/pago_fallido.html')
    
    return HttpResponseBadRequest('Método no permitido')

# Vista para reserva exitosa
def reserva_exitosa(request):
    return render(request, 'junta_vecinos/reserva_exitosa.html')

# Vista para error en la reserva
def error_reserva(request):
    error = "Hubo un problema con tu reserva."  # Puedes pasar un mensaje de error personalizado
    return render(request, 'junta_vecinos/error_reserva.html', {'error': error})

# Vista para pago fallido
def pago_fallido(request):
    return render(request, 'junta_vecinos/pago_fallido.html')


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
        'junta_nombre': "Nombre de la Junta",  # Agregar el nombre real
        'comuna': vecino.comuna,
        'region': "Metropolitana",  # Agregar la región correspondiente
        'presidente_nombre': "Nombre del Presidente",  # Agregar el nombre real del presidente
        'presidente_ci': "12345678-9",  # Agregar el CI real del presidente
    })

    # Generar el PDF usando WeasyPrint
    pdf_file = HTML(string=html_content).write_pdf()

    return pdf_file

@user_passes_test(is_admin)
@login_required
def generar_reporte_pdf(request):
    # Crear el objeto HttpResponse con el tipo de contenido de PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_reservas.pdf"'

    # Crear el PDF
    p = canvas.Canvas(response, pagesize=A4)
    ancho, alto = A4

    # Título
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, alto - 50, "Reporte de Reservas de Espacios")

    # Encabezados de la tabla
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, alto - 100, "Espacio")
    p.drawString(200, alto - 100, "Fecha")
    p.drawString(300, alto - 100, "Hora Inicio")
    p.drawString(400, alto - 100, "Hora Fin")
    p.drawString(500, alto - 100, "Usuario")

    # Listar las reservas
    p.setFont("Helvetica", 10)
    y = alto - 120
    reservas = Reserva.objects.all().order_by('fecha')
    for reserva in reservas:
        if y < 50:
            p.showPage()  # Crear nueva página si se acaba el espacio
            y = alto - 50

        p.drawString(50, y, reserva.espacio.nombre)
        p.drawString(200, y, reserva.fecha.strftime("%Y-%m-%d"))
        p.drawString(300, y, reserva.hora_inicio.strftime("%H:%M"))
        p.drawString(400, y, reserva.hora_fin.strftime("%H:%M"))
        p.drawString(500, y, f"{reserva.usuario.first_name} {reserva.usuario.last_name}")
        y -= 20

    # Finalizar el PDF
    p.showPage()
    p.save()
    
    return response

@user_passes_test(is_admin)
def crear_actividad(request):
    if request.method == 'POST':
        form = ActividadVecinalForm(request.POST, request.FILES)
        if form.is_valid():
            actividad = form.save(commit=False)
            admin = request.user.administradorcomuna
            actividad.comuna = admin
            actividad.save()
            
            # Notificar a todos los vecinos de la comuna
            vecinos = Vecino.objects.filter(comuna=admin.comuna)
            for vecino in vecinos:
                send_mail(
                    'Nueva Actividad Vecinal',
                    f'Se ha creado una nueva actividad: {actividad.titulo}\n'
                    f'Fecha: {actividad.fecha}\n'
                    f'Lugar: {actividad.lugar}\n'
                    f'Cupos disponibles: {actividad.cupo_maximo}',
                    settings.DEFAULT_FROM_EMAIL,
                    [vecino.user.email]
                )
            
            messages.success(request, 'Actividad creada exitosamente.')
            return redirect('lista_actividades')
    else:
        form = ActividadVecinalForm()
    
    return render(request, 'junta_vecinos/crear_actividad.html', {'form': form})

@login_required
def lista_actividades(request):
    if hasattr(request.user, 'administradorcomuna'):
        # Si es admin, mostrar actividades de su comuna
        actividades = ActividadVecinal.objects.filter(
            comuna=request.user.administradorcomuna
        ).order_by('fecha', 'hora_inicio')
    else:
        # Si es vecino, mostrar actividades de su comuna
        vecino = get_object_or_404(Vecino, user=request.user)
        actividades = ActividadVecinal.objects.filter(
            comuna__comuna=vecino.comuna,
            estado='activa'
        ).order_by('fecha', 'hora_inicio')

        # Añadir información de inscripción para cada actividad
        for actividad in actividades:
            actividad.usuario_inscrito = InscripcionActividad.objects.filter(
                actividad=actividad,
                vecino=vecino
            ).exists()
    
    return render(request, 'junta_vecinos/lista_actividades.html', {
        'actividades': actividades
    })

@login_required
def inscribir_actividad(request, actividad_id):
    actividad = get_object_or_404(ActividadVecinal, id=actividad_id)
    vecino = get_object_or_404(Vecino, user=request.user)
    
    if actividad.esta_llena():
        messages.error(request, 'Lo sentimos, esta actividad ya no tiene cupos disponibles.')
        return redirect('lista_actividades')
    
    if request.method == 'POST':
        try:
            
            # Crear transacción en WebPay
            buy_order = f"ACT-{actividad.id}-{vecino.user.id}-{int(datetime.now().timestamp())}"
            session_id = request.session.session_key
            return_url = request.build_absolute_uri(reverse('webpay_retorno_actividad'))
            monto = str(actividad.precio) 
            
            transaction = Transaction()
            response = transaction.create(buy_order, session_id, monto, return_url)

            # Guardar en la sesión los datos de inscripción
            request.session['inscripcion_pendiente'] = {
                'actividad_id': actividad.id,
                'monto': monto,
                'buy_order': buy_order
            }

            return JsonResponse({
                'success': True,
                'payment_url': response['url'],
                'token': response['token']
            })
        
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@csrf_exempt
def webpay_retorno_actividad(request):
    if request.method == 'POST' or request.method == 'GET':
        token = request.POST.get('token_ws') if request.method == 'POST' else request.GET.get('token_ws')
        
        if not token:
            return render(request, 'junta_vecinos/error_inscripcion.html', {'error': 'Token de pago no recibido'})
        
        transaction = Transaction()
        response = transaction.commit(token)

        if response['response_code'] == 0:
            inscripcion_data = request.session.get('inscripcion_pendiente')
            if inscripcion_data and inscripcion_data['buy_order'] == response['buy_order']:
                # Crear la inscripción
                actividad = get_object_or_404(ActividadVecinal, id=inscripcion_data['actividad_id'])
                vecino = get_object_or_404(Vecino, user=request.user)
                InscripcionActividad.objects.create(actividad=actividad, vecino=vecino)
                actividad.cupo_actual += 1
                actividad.save()

                # Eliminar datos de inscripción de la sesión
                del request.session['inscripcion_pendiente']
                return render(request, 'junta_vecinos/inscripcion_exitosa.html', {'actividad': actividad})
            else:
                return render(request, 'junta_vecinos/error_inscripcion.html', {'error': 'Datos de inscripción no coinciden'})
        else:
            return render(request, 'junta_vecinos/pago_fallido.html')
    
    return HttpResponseBadRequest('Método no permitido')

def inscripcion_exitosa(request):
    actividad_id = request.session.get('inscripcion_pendiente', {}).get('actividad_id')
    actividad = get_object_or_404(ActividadVecinal, id=actividad_id)
    return render(request, 'junta_vecinos/inscripcion_exitosa.html', {'actividad': actividad})

def error_inscripcion(request):
    error_message = request.GET.get('error', 'Ha ocurrido un error desconocido.')
    return render(request, 'junta_vecinos/error_inscripcion.html', {'error': error_message})

@user_passes_test(is_admin)
def cancelar_actividad(request, actividad_id):
    actividad = get_object_or_404(ActividadVecinal, id=actividad_id)
    
    if request.method == 'POST':
        actividad.estado = 'cancelada'
        actividad.save()
        
        # Notificar a los inscritos
        inscripciones = InscripcionActividad.objects.filter(actividad=actividad)
        for inscripcion in inscripciones:
            send_mail(
                'Actividad Vecinal Cancelada',
                f'La actividad {actividad.titulo} ha sido cancelada.\n'
                f'Lamentamos los inconvenientes causados.',
                settings.DEFAULT_FROM_EMAIL,
                [inscripcion.vecino.user.email]
            )
        
        messages.success(request, 'Actividad cancelada exitosamente.')
        return redirect('lista_actividades')
    
    return render(request, 'junta_vecinos/cancelar_actividad.html', {
        'actividad': actividad
    })

@user_passes_test(is_admin)
def registrar_asistencia(request, actividad_id):
    actividad = get_object_or_404(ActividadVecinal, id=actividad_id)
    inscripciones = InscripcionActividad.objects.filter(actividad=actividad)
    
    if request.method == 'POST':
        asistentes = request.POST.getlist('asistentes')
        
        for inscripcion in inscripciones:
            inscripcion.asistio = str(inscripcion.id) in asistentes
            inscripcion.save()
        
        messages.success(request, 'Asistencia registrada exitosamente.')
        return redirect('lista_actividades')
    
    return render(request, 'junta_vecinos/registrar_asistencia.html', {
        'actividad': actividad,
        'inscripciones': inscripciones
    })