from django.db import models
from django.contrib.auth.models import User

# Modelo para representar a un vecino
class Vecino(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nombres = models.CharField(max_length=255, default='Desconocido')
    apellidos = models.CharField(max_length=255, default='Desconocido')
    direccion = models.CharField(max_length=255)
    telefono = models.CharField(max_length=15)
    fecha_nacimiento = models.DateField()

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"
    
class SolicitudCertificado(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]

    vecino = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_solicitud = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='pendiente')
    motivo = models.TextField()

    # Nuevos campos para los archivos
    foto_carnet_frente = models.ImageField(upload_to='carnets/', blank=False, null=False)
    foto_carnet_atras = models.ImageField(upload_to='carnets/', blank=False, null=False)
    documento_residencia = models.FileField(upload_to='documentos_residencia/', blank=False, null=False)

    def __str__(self):
        return f"Solicitud de {self.vecino.get_full_name()} - {self.get_estado_display()}"

class CertificadoResidencia(models.Model):
    solicitud = models.OneToOneField(SolicitudCertificado, on_delete=models.CASCADE)
    numero_certificado = models.CharField(max_length=20, unique=True)
    fecha_emision = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Certificado {self.numero_certificado} para {self.solicitud.vecino.get_full_name()}"

# Modelo para representar un proyecto vecinal
class ProyectoVecinal(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechaz', 'Rechazado'),
    ]

    vecino = models.ForeignKey(Vecino, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=255)
    descripcion = models.TextField()
    fecha_postulacion = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='pendiente')
    resolucion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.titulo

# Modelo para representar una notificación
class Notificacion(models.Model):
    titulo = models.CharField(max_length=255)
    mensaje = models.TextField()
    fecha_envio = models.DateTimeField(auto_now_add=True)
    destinatarios = models.ManyToManyField(Vecino)

    def __str__(self):
        return self.titulo

# Modelo para representar una noticia
class Noticia(models.Model):
    titulo = models.CharField(max_length=255)
    contenido = models.TextField()
    fecha_publicacion = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.titulo

# Modelo para representar una solicitud de uso de instalaciones
class SolicitudInstalacion(models.Model):
    vecino = models.ForeignKey(Vecino, on_delete=models.CASCADE)
    instalacion = models.CharField(max_length=255)
    fecha_solicitud = models.DateField(auto_now_add=True)
    uso = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    estado = models.CharField(max_length=10, choices=ProyectoVecinal.ESTADO_CHOICES, default='pendiente')

    def __str__(self):
        return f"{self.instalacion} - {self.vecino}"

# Modelo para representar una actividad vecinal
class ActividadVecinal(models.Model):
    titulo = models.CharField(max_length=255)
    descripcion = models.TextField()
    fecha_actividad = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    cupo_maximo = models.PositiveIntegerField()
    inscritos = models.ManyToManyField(Vecino, through='InscripcionActividad')

    def __str__(self):
        return self.titulo

# Modelo intermedio para representar la inscripción a una actividad vecinal
class InscripcionActividad(models.Model):
    vecino = models.ForeignKey(Vecino, on_delete=models.CASCADE)
    actividad = models.ForeignKey(ActividadVecinal, on_delete=models.CASCADE)
    fecha_inscripcion = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.vecino} inscrito en {self.actividad}"
