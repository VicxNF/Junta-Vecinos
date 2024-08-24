from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('vecinos/', views.lista_vecinos, name='lista_vecinos'),
    path('proyectos/', views.lista_proyectos, name='lista_proyectos'),
    path('registro/', views.registro_vecino, name='registro_vecino'),
    # Agrega más rutas según sea necesario
]
