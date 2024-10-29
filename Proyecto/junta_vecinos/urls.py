from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.bienvenida, name='bienvenida'),
    path('inicio/', views.index, name='index'),
    path('vecinos/', views.lista_vecinos, name='lista_vecinos'),
    path('registro/', views.registro_vecino, name='registro_vecino'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('registros/', views.solicitudes_registro, name='solicitudes_registro'),
    path('aprobar/<int:solicitud_id>/', views.aprobar_registro, name='aprobar_registro'),
    path('rechazar/<int:solicitud_id>/', views.rechazar_registro, name='rechazar_registro'),
    path('solicitar/', views.solicitar_certificado, name='solicitar_certificado'),
    path('gestionar/', views.gestionar_solicitudes, name='gestionar_solicitudes'),
    path('ver-solicitud/<int:id>/', views.ver_solicitud, name='ver_solicitud'),
    path('aprobar-solicitud/<int:id>/', views.aprobar_solicitud, name='aprobar_solicitud'),
    path('rechazar-solicitud/<int:id>/', views.rechazar_solicitud, name='rechazar_solicitud'),
    path('solicitud/<int:id>/enviar/', views.enviar_certificado, name='enviar_certificado'),
    path('solicitud/<int:id>/rechazar/', views.rechazar_solicitud, name='rechazar_solicitud'),
    path('proyectos/crear/', views.crear_proyecto, name='crear_proyecto'),
    path('proyectos/mis-proyectos/', views.mis_proyectos, name='mis_proyectos'),
    path('proyectos/<int:proyecto_id>/', views.detalle_proyecto, name='detalle_proyecto'),
    path('administracion/proyectos/', views.admin_proyectos, name='admin_proyectos'),
    path('administracion/proyectos/<int:proyecto_id>/evaluar/', views.evaluar_proyecto, name='evaluar_proyecto'),
    path('proyectos/comuna/', views.proyectos_comuna, name='proyectos_comuna'),
    path('proyectos/<int:proyecto_id>/postular/', views.postular_proyecto, name='postular_proyecto'),
    path('proyectos/<int:proyecto_id>/postulaciones/', views.gestionar_postulaciones, name='gestionar_postulaciones'),
    path('noticias/publicar/', views.publicar_noticia, name='publicar_noticia'),
    path('noticias/gestionar/', views.gestionar_noticias, name='gestionar_noticias'),
    path('noticia/<int:id>/editar/', views.editar_noticia, name='editar_noticia'),
    path('registrar_espacio/', views.registrar_espacio, name='registrar_espacio'),
    path('lista_espacios/', views.lista_espacios, name='lista_espacios'),
    path('editar_espacio/<int:espacio_id>/', views.editar_espacio, name='editar_espacio'),
    path('eliminar_espacio/<int:espacio_id>/', views.eliminar_espacio, name='eliminar_espacio'),
    path('espacios/', views.espacios_disponibles, name='espacios_disponibles'),
    path('espacio/<int:espacio_id>/reservar/', views.reservar_espacio, name='reservar_espacio'),
    path('reservas/', views.lista_reservas, name='lista_reservas'),
    path('api/get-available-slots/', views.get_available_slots, name='get_available_slots'),
    path('generar_reporte_pdf/', views.generar_reporte_pdf, name='generar_reporte_pdf'),
    path('generar_reporte_solicitudes_pdf/', views.generar_reporte_solicitudes_pdf, name='generar_reporte_solicitudes_pdf'),
    path('api/get-espacio-info/', views.get_espacio_info, name='get_espacio_info'),
    path('espacio/<int:espacio_id>/reservar/', views.reservar_espacio, name='reservar_espacio'),
    path('webpay-retorno/', views.webpay_retorno, name='webpay_retorno'),
    path('reserva-exitosa/', views.reserva_exitosa, name='reserva_exitosa'),
    path('error-reserva/', views.error_reserva, name='error_reserva'),
    path('pago-fallido/', views.pago_fallido, name='pago_fallido'),
    path('actividades/', views.lista_actividades, name='lista_actividades'),
    path('actividades/crear/', views.crear_actividad, name='crear_actividad'),
    path('actividades/<int:actividad_id>/inscribir/', views.inscribir_actividad, name='inscribir_actividad'),
    path('actividades/<int:actividad_id>/cancelar/', views.cancelar_actividad, name='cancelar_actividad'),
    path('actividades/<int:actividad_id>/asistencia/', views.registrar_asistencia, name='registrar_asistencia'),
    path('noticia/<int:noticia_id>/', views.detalle_noticia, name='detalle_noticia'),
    path('webpay/retorno_actividad/', views.webpay_retorno_actividad, name='webpay_retorno_actividad'),
    path('actividades/inscripcion-exitosa/', views.inscripcion_exitosa, name='inscripcion_exitosa'),
    path('actividades/error-inscripcion/', views.error_inscripcion, name='error_inscripcion'),
]
    # Agrega más rutas según sea necesario
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)