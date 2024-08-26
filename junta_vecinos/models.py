from django.db import models
from django.contrib.auth.models import User

# Modelo para representar a un vecino
class Vecino(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nombres = models.CharField(max_length=255)
    apellidos = models.CharField(max_length=255)
    direccion = models.CharField(max_length=255)
    telefono = models.CharField(max_length=15)
    fecha_nacimiento = models.DateField()

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"
    
class SolicitudCertificado(models.Model):
    ESTADO_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('Aprobado', 'Aprobado'),
        ('Rechazado', 'Rechazado'),
    ]

    vecino = models.ForeignKey(Vecino, on_delete=models.CASCADE)  # Cambio aquí
    fecha_solicitud = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='pendiente')
    motivo = models.TextField()

    # Nuevos campos para los archivos
    foto_carnet_frente = models.ImageField(upload_to='carnets/', blank=False, null=False)
    foto_carnet_atras = models.ImageField(upload_to='carnets/', blank=False, null=False)
    documento_residencia = models.FileField(upload_to='documentos_residencia/', blank=False, null=False)

    def __str__(self):
        return f"Solicitud de {self.vecino} - {self.get_estado_display()}"

class CertificadoResidencia(models.Model):
    vecino = models.ForeignKey(Vecino, on_delete=models.CASCADE)
    fecha_emision = models.DateField(auto_now_add=True)
    numero_certificado = models.CharField(max_length=20, unique=True)
    documento_certificado = models.FileField(upload_to='certificados/', null=True, blank=True)

    def __str__(self):
        return f"Certificado {self.numero_certificado} - {self.vecino}"

class ProyectoVecinal(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]

    vecino = models.ForeignKey(Vecino, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=255)
    descripcion = models.TextField()
    fecha_postulacion = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='pendiente')
    archivo_propuesta = models.FileField(upload_to='propuestas_proyectos/', blank=True, null=True)

    def __str__(self):
        return f"{self.titulo} - {self.get_estado_display()}"