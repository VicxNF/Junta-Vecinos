from django.contrib import admin
from .models import *
from django.contrib import messages
from django.urls import path
from django.http import HttpResponseRedirect
from django.utils.html import format_html


admin.site.register(Vecino)
admin.site.register(CertificadoResidencia)
admin.site.register(SolicitudCertificado)
admin.site.register(ProyectoVecinal)
admin.site.register(Noticia)
admin.site.register(Espacio)
admin.site.register(Reserva)
admin.site.register(SolicitudRegistroVecino)
admin.site.register(ActividadVecinal)
admin.site.register(InscripcionActividad)
@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_email', 'timestamp', 'was_successful', 'ip_address', 'is_user_currently_locked', 'unlock_button')
    list_filter = ('was_successful', 'timestamp')
    search_fields = ('user__username', 'user__email', 'ip_address')
    date_hierarchy = 'timestamp'
    actions = ['unlock_users']

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'

    def is_user_currently_locked(self, obj):
        return LoginAttempt.is_user_locked(obj.user)
    is_user_currently_locked.boolean = True
    is_user_currently_locked.short_description = "¿Bloqueado?"

    def unlock_button(self, obj):
        if self.is_user_currently_locked(obj):
            return format_html(
                '<a class="button" href="{}">Desbloquear</a>',
                f'unlock-user/{obj.user.id}/'
            )
        return "No bloqueado"
    unlock_button.short_description = 'Acción'
    unlock_button.allow_tags = True

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'unlock-user/<int:user_id>/',
                self.admin_site.admin_view(self.unlock_user_view),
                name='unlock-user',
            ),
        ]
        return custom_urls + urls
    
    def unlock_user_view(self, request, user_id):
        deleted_count = LoginAttempt.objects.filter(
            user_id=user_id,
            was_successful=False
        ).delete()[0]
        
        if deleted_count:
            messages.success(request, 'Usuario desbloqueado exitosamente.')
        else:
            messages.info(request, 'El usuario no estaba bloqueado.')
        
        return HttpResponseRedirect("../../")

    def unlock_users(self, request, queryset):
        users = set(queryset.values_list('user', flat=True))
        deleted_count = LoginAttempt.objects.filter(
            user__in=users,
            was_successful=False
        ).delete()[0]
        
        if deleted_count:
            messages.success(
                request,
                f'Se han eliminado {deleted_count} intentos fallidos. Los usuarios seleccionados han sido desbloqueados.'
            )
        else:
            messages.info(request, 'No había intentos fallidos para eliminar.')
    unlock_users.short_description = "Desbloquear usuarios seleccionados"

    def has_add_permission(self, request):
        return False  # Deshabilita la creación manual de intentos de login
    
@admin.register(AdministradorComuna)
class AdministradorComunaAdmin(admin.ModelAdmin):
    list_display = ['comuna', 'get_presidente_nombre_completo', 'presidente_rut']
    search_fields = ['presidente_nombre', 'presidente_apellidos', 'presidente_rut']
    list_filter = ['comuna']
    fieldsets = (
        ('Información de Usuario', {
            'fields': ('user', 'comuna')
        }),
        ('Información del Presidente', {
            'fields': ('presidente_nombre', 'presidente_apellidos', 'presidente_rut', 'firma_presidente')
        }),
    )