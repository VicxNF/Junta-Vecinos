from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
import uuid

class AdministradorComuna(models.Model):
    COMUNA_CHOICES = [
        ('ÑUÑOA', 'Ñuñoa'),
        ('PUENTE_ALTO', 'Puente Alto'),
        ('LA_FLORIDA', 'La Florida'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    comuna = models.CharField(max_length=20, choices=COMUNA_CHOICES, unique=True)
    presidente_nombre = models.CharField(max_length=100, verbose_name="Nombre del Presidente", default="")
    presidente_apellidos = models.CharField(max_length=100, verbose_name="Apellidos del Presidente", default="")
    presidente_rut = models.CharField(max_length=12, verbose_name="RUT del Presidente", default="")
    firma_presidente = models.ImageField(
        upload_to='firmas_presidentes/',
        null=True,
        blank=True,
        verbose_name="Firma del Presidente"
    )

    def get_presidente_nombre_completo(self):
        return f"{self.presidente_nombre} {self.presidente_apellidos}"

    def __str__(self):
        return f"Administrador de {self.get_comuna_display()} - Presidente: {self.get_presidente_nombre_completo()}"
    
class TokenRegistro(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        return not self.expires_at < timezone.now()
    
class LoginAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    was_successful = models.BooleanField(default=False)
    
    @classmethod
    def get_recent_attempts(cls, user, minutes=30):
        time_threshold = timezone.now() - timedelta(minutes=minutes)
        return cls.objects.filter(
            user=user,
            timestamp__gte=time_threshold,
            was_successful=False
        ).count()
    
    @classmethod
    def is_user_locked(cls, user):
        MAX_ATTEMPTS = 3
        LOCKOUT_DURATION = 30  # minutos
        recent_attempts = cls.get_recent_attempts(user, LOCKOUT_DURATION)
        return recent_attempts >= MAX_ATTEMPTS

    @classmethod
    def get_attempts_left(cls, user):
        MAX_ATTEMPTS = 3
        return MAX_ATTEMPTS - cls.get_recent_attempts(user)



# Modelo para representar a un vecino
class Vecino(models.Model):
    COMUNA_CHOICES = [
        ('ÑUÑOA', 'Ñuñoa'),
        ('PUENTE_ALTO', 'Puente Alto'),
        ('LA_FLORIDA', 'La Florida'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nombres = models.CharField(max_length=255)
    apellidos = models.CharField(max_length=255)
    direccion = models.CharField(max_length=255)
    telefono = models.CharField(max_length=15)
    fecha_nacimiento = models.DateField()
    rut = models.CharField(max_length=12, unique=True)
    comuna = models.CharField(max_length=20, choices=COMUNA_CHOICES, default='ÑUÑOA')
    administrador = models.ForeignKey(AdministradorComuna, on_delete=models.SET_NULL, null=True, related_name='vecinos')

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"

    def save(self, *args, **kwargs):
        if not self.administrador:
            self.administrador = AdministradorComuna.objects.get(comuna=self.comuna)
        super().save(*args, **kwargs)

class TokenReestablecerContrasena(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=32)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField()
    usado = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Token de reestablecimiento de contraseña"
        verbose_name_plural = "Tokens de reestablecimiento de contraseña"


class SolicitudRegistroVecino(models.Model):
    vecino = models.OneToOneField(Vecino, on_delete=models.CASCADE)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Solicitud de registro para {self.vecino.nombres} {self.vecino.apellidos}"
    
class SolicitudCertificado(models.Model):
    ESTADO_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('Aprobado', 'Aprobado'),
        ('Rechazado', 'Rechazado'),
    ]

    vecino = models.ForeignKey(Vecino, on_delete=models.CASCADE)  # Cambio aquí
    fecha_solicitud = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='Pendiente')
    motivo = models.TextField()
    foto_carnet_frente = models.ImageField(upload_to='carnets/', blank=False, null=False)
    foto_carnet_atras = models.ImageField(upload_to='carnets/', blank=False, null=False)
    documento_residencia = models.ImageField(upload_to='documentos_residencia/', blank=False, null=False)

    def __str__(self):
        return f"Solicitud de {self.vecino} - {self.get_estado_display()}"

class CertificadoResidencia(models.Model):
    vecino = models.ForeignKey(Vecino, on_delete=models.CASCADE)
    numero_certificado = models.CharField(max_length=50)
    documento_certificado = models.FileField(upload_to='certificados/')
    fecha_emision = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Certificado {self.numero_certificado} - {self.vecino}"

class ProyectoVecinal(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]

    vecino = models.ForeignKey(Vecino, on_delete=models.CASCADE)
    propuesta = models.CharField(max_length=255)  # Cambiado de titulo a propuesta
    descripcion = models.TextField()
    fecha_postulacion = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='pendiente')
    evidencia = models.ImageField(upload_to='evidencias/', blank=True, null=True)  # Campo evidencia
    razon_rechazo = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.propuesta} - {self.get_estado_display()}"
    
class PostulacionProyecto(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aceptada', 'Aceptada'),
        ('rechazada', 'Rechazada')
    ]
    
    proyecto = models.ForeignKey('ProyectoVecinal', on_delete=models.CASCADE, related_name='postulaciones')
    vecino = models.ForeignKey('Vecino', on_delete=models.CASCADE, related_name='postulaciones_proyectos')
    fecha_postulacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='pendiente')
    motivo = models.TextField(help_text="¿Por qué quieres participar en este proyecto?")
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('proyecto', 'vecino')
        
    def __str__(self):
        return f"Postulación de {self.vecino} a {self.proyecto}"


class Noticia(models.Model):
    titulo = models.CharField(max_length=255)
    contenido = models.TextField()
    fecha_publicacion = models.DateField(auto_now_add=True)
    imagen = models.ImageField(upload_to='imagenes_noticias/', blank=True, null=True)
    comuna = models.ForeignKey(AdministradorComuna, on_delete=models.CASCADE, related_name='noticias')

    def __str__(self):
        return self.titulo


class Espacio(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    capacidad = models.IntegerField()
    foto = models.ImageField(upload_to='espacios/', null=True, blank=True)
    ubicacion = models.CharField(max_length=200, default='Ubicación no disponible')
    precio_por_hora = models.DecimalField(max_digits=10, decimal_places=2)
    comuna = models.ForeignKey(AdministradorComuna, on_delete=models.CASCADE, related_name='espacios')

    def __str__(self):
        return self.nombre

class Reserva(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    espacio = models.ForeignKey(Espacio, on_delete=models.CASCADE)
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))  # Agrega este campo

    def __str__(self):
        return f"{self.espacio.nombre} reservado por {self.usuario.username} el {self.fecha} de {self.hora_inicio} a {self.hora_fin}"
    
class ActividadVecinal(models.Model):
    ESTADO_CHOICES = [
        ('activa', 'Activa'),
        ('cancelada', 'Cancelada'),
        ('finalizada', 'Finalizada'),
    ]

    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    lugar = models.CharField(max_length=200)
    cupo_maximo = models.PositiveIntegerField()
    cupo_actual = models.PositiveIntegerField(default=0)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='activa')
    imagen = models.ImageField(upload_to='actividades/', null=True, blank=True)
    comuna = models.ForeignKey('AdministradorComuna', on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    def espacios_disponibles(self):
        return self.cupo_maximo - self.cupo_actual

    def esta_llena(self):
        return self.cupo_actual >= self.cupo_maximo

class InscripcionActividad(models.Model):
    actividad = models.ForeignKey(ActividadVecinal, on_delete=models.CASCADE)
    vecino = models.ForeignKey('Vecino', on_delete=models.CASCADE)
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)
    asistio = models.BooleanField(default=False)

    class Meta:
        unique_together = ('actividad', 'vecino')    