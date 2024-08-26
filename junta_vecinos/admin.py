from django.contrib import admin
from .models import Vecino, CertificadoResidencia, SolicitudCertificado, ProyectoVecinal

admin.site.register(Vecino)
admin.site.register(CertificadoResidencia)
admin.site.register(SolicitudCertificado)
admin.site.register(ProyectoVecinal)