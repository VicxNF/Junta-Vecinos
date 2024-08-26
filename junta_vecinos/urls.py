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
    path('solicitar/', views.solicitar_certificado, name='solicitar_certificado'),
    path('gestionar/', views.gestionar_solicitudes, name='gestionar_solicitudes'),
    path('ver-solicitud/<int:id>/', views.ver_solicitud, name='ver_solicitud'),
    path('aprobar-solicitud/<int:id>/', views.aprobar_solicitud, name='aprobar_solicitud'),
    path('rechazar-solicitud/<int:id>/', views.rechazar_solicitud, name='rechazar_solicitud'),
    path('solicitud/<int:id>/enviar/', views.enviar_certificado, name='enviar_certificado'),
    path('solicitud/<int:id>/rechazar/', views.rechazar_solicitud, name='rechazar_solicitud'),
    path('postular-proyecto/', views.postular_proyecto, name='postular_proyecto'),
    path('gestionar-proyectos/', views.gestionar_proyectos, name='gestionar_proyectos'),
    path('proyecto/<int:id>/ver/', views.ver_proyecto, name='ver_proyecto'),
    path('proyecto/<int:id>/aprobar/', views.aprobar_proyecto, name='aprobar_proyecto'),
    path('proyecto/<int:id>/rechazar/', views.rechazar_proyecto, name='rechazar_proyecto'),
    # Agrega más rutas según sea necesario
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)