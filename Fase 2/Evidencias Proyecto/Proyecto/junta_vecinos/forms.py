from django import forms
from django.contrib.auth.models import User
from .models import *
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

class RegistroVecinoForm(forms.ModelForm):
    nombres = forms.CharField(label="Nombres", max_length=255)
    apellidos = forms.CharField(label="Apellidos", max_length=255)
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
    email = forms.EmailField(label="Correo Electrónico")
    fecha_nacimiento = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label="Fecha de Nacimiento")
    rut = forms.CharField(label="RUT", max_length=12)
    comuna = forms.ChoiceField(label="Comuna", choices=Vecino.COMUNA_CHOICES)

    class Meta:
        model = Vecino
        fields = ['nombres', 'apellidos', 'direccion', 'telefono', 'fecha_nacimiento', 'rut', 'comuna']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo electrónico ya está en uso.")
        return email

    def clean_rut(self):
        rut = self.cleaned_data.get('rut')
        if Vecino.objects.filter(rut=rut).exists():
            raise forms.ValidationError("Este RUT ya está registrado.")
        return rut

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['email'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['nombres'],
            last_name=self.cleaned_data['apellidos'],
            is_active=False  # El usuario no estará activo hasta confirmar
        )
        
        vecino = super().save(commit=False)
        vecino.user = user
        vecino.comuna = self.cleaned_data['comuna']
        
        try:
            administrador = AdministradorComuna.objects.get(comuna=vecino.comuna)
            vecino.administrador = administrador
        except AdministradorComuna.DoesNotExist:
            pass
        
        if commit:
            vecino.save()
            
            # Crear token de registro
            token_registro = TokenRegistro.objects.create(
                user=user, 
                expires_at=timezone.now() + timedelta(hours=24)
            )
        
        return vecino

    
class SolicitudCertificadoForm(forms.ModelForm):
    class Meta:
        model = SolicitudCertificado
        fields = ['motivo', 'foto_carnet_frente', 'foto_carnet_atras', 'documento_residencia']
        widgets = {
            'motivo': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Especifique el motivo de la solicitud'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['foto_carnet_frente'].label = 'Foto del Carnet (Parte Frontal)'
        self.fields['foto_carnet_atras'].label = 'Foto del Carnet (Parte Trasera)'
        self.fields['documento_residencia'].label = 'Documento que Certifique su Residencia'
        
        # Validación de archivos de imagen
        for field_name in ['foto_carnet_frente', 'foto_carnet_atras', 'documento_residencia']:
            self.fields[field_name].validators.append(
                FileExtensionValidator(
                    allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'bmp'],
                    message='Por favor, suba solo archivos de imagen (jpg, jpeg, png, gif, bmp).'
                )
            )

class DocumentoCertificadoForm(forms.ModelForm):
    class Meta:
        model = CertificadoResidencia
        fields = ['documento_certificado']

class LoginForm(forms.Form):
    TIPO_USUARIO_CHOICES = [
        ('vecino', 'Vecino'),
        ('administrador', 'Administrador')
    ]
    
    tipo_usuario = forms.ChoiceField(
        label="Tipo de Usuario",
        choices=TIPO_USUARIO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label="Correo Electrónico",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        
        if email:
            try:
                user = User.objects.get(email=email)
                if LoginAttempt.is_user_locked(user):
                    raise forms.ValidationError(
                        "Tu cuenta está temporalmente bloqueada por múltiples intentos fallidos. "
                        "Por favor, intenta nuevamente en 30 minutos."
                    )
            except User.DoesNotExist:
                pass
        
        return cleaned_data


class EnviarCertificadoForm(forms.ModelForm):
    contenido_correo = forms.CharField(widget=forms.Textarea(attrs={'rows': 5, 'placeholder': 'Escribe el contenido del correo'}), label="Contenido del Correo")
    documento_certificado = forms.FileField(label="Documento del Certificado")

    class Meta:
        model = CertificadoResidencia
        fields = ['documento_certificado']

class RechazoCertificadoForm(forms.Form):
    mensaje_rechazo = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Escribe las razones del rechazo...'}),
        label="Mensaje de Rechazo"
    )

class ProyectoVecinalForm(forms.ModelForm):
    class Meta:
        model = ProyectoVecinal
        fields = ['propuesta', 'descripcion', 'evidencia']
        widgets = {
            'propuesta': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Huerto Comunitario',
                'required': True,
                'maxlength': 255
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe tu proyecto, sus objetivos y beneficios para la comunidad...',
                'required': True,
                'maxlength': 1000
            }),
            'evidencia': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
    
    def clean_evidencia(self):
        evidencia = self.cleaned_data.get('evidencia')
        if evidencia:
            if evidencia.size > 5 * 1024 * 1024:  # 5MB
                raise forms.ValidationError('El archivo es demasiado grande. El tamaño máximo es 5MB.')
            if not evidencia.content_type.startswith('image/'):
                raise forms.ValidationError('Solo se permiten archivos de imagen.')
        return evidencia

        # Validación de archivos de imagen
        for field_name in ['evidencia']:
            self.fields[field_name].validators.append(
                FileExtensionValidator(
                    allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'bmp'],
                    message='Por favor, suba solo archivos de imagen (jpg, jpeg, png, gif, bmp).'
                )
            )
        
    def clean_evidencia(self):
        evidencia = self.cleaned_data.get('evidencia')
        if evidencia:
            if evidencia.size > 5 * 1024 * 1024:  # 5MB
                raise forms.ValidationError('El archivo es demasiado grande. El tamaño máximo es 5MB.')
            if not evidencia.content_type.startswith('image/'):
                raise forms.ValidationError('Solo se permiten archivos de imagen.')
        return evidencia

class PostulacionProyectoForm(forms.ModelForm):
    class Meta:
        model = PostulacionProyecto
        fields = ['motivo']
        widgets = {
            'motivo': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Explica por qué te gustaría participar en este proyecto'
            })
        }


class CorreoAprobacionForm(forms.Form):
    contenido_correo = forms.CharField(
        label='Contenido del Correo de Aprobación',
        widget=forms.Textarea(attrs={
            'rows': 5,
            'placeholder': 'Escribe el contenido del correo aquí...',
            'class': 'form-control'
        }),
        required=True
    )

class CorreoRechazoForm(forms.Form):
    contenido = forms.CharField(widget=forms.Textarea(attrs={'rows': 5}), label='Contenido del correo')


class NoticiaForm(forms.ModelForm):
    class Meta:
        model = Noticia
        fields = ['titulo', 'contenido', 'imagen']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingresa un título llamativo',
                'maxlength': 255,
            }),
            'contenido': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Escribe el contenido de la noticia...',
                'maxlength': 1000,
            }),
            'imagen': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].error_messages = {
                'required': f'El campo {field} es obligatorio.',
                'invalid': f'El valor ingresado para {field} no es válido.'
            }

    def clean_imagen(self):
        imagen = self.cleaned_data.get('imagen')
        if imagen:
            # Validar el tamaño máximo (5MB)
            if imagen.size > 5 * 1024 * 1024:
                raise forms.ValidationError('La imagen no debe superar los 5MB')
            
            # Validar extensiones permitidas
            allowed_extensions = ['jpg', 'jpeg', 'png', 'gif']
            ext = imagen.name.split('.')[-1].lower()
            if ext not in allowed_extensions:
                raise forms.ValidationError('Formato de imagen no válido. Use: jpg, jpeg, png o gif')
        
        return imagen

class EspacioForm(forms.ModelForm):
    class Meta:
        model = Espacio
        fields = ['nombre', 'descripcion', 'capacidad', 'foto', 'ubicacion', 'precio_por_hora']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control'}),
            'capacidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'ubicacion': forms.TextInput(attrs={'class': 'form-control'}),
            'precio_por_hora': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.admin = kwargs.pop('admin', None)
        super(EspacioForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        espacio = super(EspacioForm, self).save(commit=False)
        if self.admin:
            espacio.comuna = self.admin.administradorcomuna
        if commit:
            espacio.save()
        return espacio

class RechazoForm(forms.Form):
    razon_rechazo = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Escriba la razón del rechazo...', 'rows': 3}),
        label='Razón del Rechazo',
        max_length=500,
        required=True
    )

class AprobacionForm(forms.Form):
    contenido_correo = forms.CharField(
        label='Contenido del Correo de Aprobación',
        widget=forms.Textarea(attrs={
            'rows': 5,  # Número de filas del textarea
            'placeholder': 'Escribe el contenido del correo aquí...',  # Texto de ejemplo
            'class': 'form-control'  # Clase CSS para aplicar el estilo
        }),
        required=True  # Campo obligatorio
    )


class ActividadVecinalForm(forms.ModelForm):
    # Cambiamos el campo lugar por un ModelChoiceField
    lugar = forms.ModelChoiceField(
        queryset=Espacio.objects.none(),  # Inicialmente vacío, se poblará en __init__
        empty_label="Seleccione un espacio",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = ActividadVecinal
        fields = ['titulo', 'descripcion', 'fecha', 'hora_inicio', 'hora_fin', 
                 'lugar', 'cupo_maximo', 'imagen', 'precio']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'hora_fin': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'cupo_maximo': forms.NumberInput(attrs={'class': 'form-control'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'imagen': forms.FileInput(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, admin=None, **kwargs):
        super().__init__(*args, **kwargs)
        if admin:
            # Ahora admin ya es el AdministradorComuna
            self.fields['lugar'].queryset = Espacio.objects.filter(comuna=admin)

class FormularioSolicitudReestablecerContrasena(forms.Form):
    correo = forms.EmailField(label='Correo Electrónico')

    def clean_correo(self):
        correo = self.cleaned_data['correo']
        if not User.objects.filter(email=correo).exists():
            raise forms.ValidationError("No existe una cuenta con este correo electrónico.")
        return correo

class FormularioNuevaContrasena(forms.Form):
    contrasena1 = forms.CharField(
        label='Nueva Contraseña',
        widget=forms.PasswordInput,
        min_length=8
    )
    contrasena2 = forms.CharField(
        label='Confirmar Nueva Contraseña',
        widget=forms.PasswordInput
    )

    def clean(self):
        datos_limpios = super().clean()
        contrasena1 = datos_limpios.get('contrasena1')
        contrasena2 = datos_limpios.get('contrasena2')
        if contrasena1 and contrasena2:
            if contrasena1 != contrasena2:
                raise forms.ValidationError("Las contraseñas no coinciden.")
        return datos_limpios