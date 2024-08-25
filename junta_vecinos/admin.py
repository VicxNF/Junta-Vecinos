from django.contrib import admin
from .models import Vecino, CertificadoResidencia, SolicitudCertificado

admin.site.register(Vecino)
admin.site.register(CertificadoResidencia)
admin.site.register(SolicitudCertificado)