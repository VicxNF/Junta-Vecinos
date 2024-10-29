from django import forms
from django.contrib.auth.models import User
from .models import *
from django.core.exceptions import ValidationError

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
            last_name=self.cleaned_data['apellidos']
        )
        user.is_active = False
        user.save()
        
        vecino = super().save(commit=False)
        vecino.user = user
        vecino.comuna = self.cleaned_data['comuna']
        
        try:
            administrador = AdministradorComuna.objects.get(comuna=vecino.comuna)
            vecino.administrador = administrador
        except AdministradorComuna.DoesNotExist:
            # Manejar el caso en que no exista un administrador para la comuna
            # Podrías lanzar una excepción, establecer un valor por defecto, o manejarlo de otra manera
            pass
        
        if commit:
            vecino.save()
            SolicitudRegistroVecino.objects.create(vecino=vecino)
        
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

class DocumentoCertificadoForm(forms.ModelForm):
    class Meta:
        model = CertificadoResidencia
        fields = ['documento_certificado']

class LoginForm(forms.Form):
    email = forms.EmailField(label="Correo Electrónico")
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        # Verificar si el usuario existe y las credenciales son correctas
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise forms.ValidationError("El correo electrónico no está registrado.")

        if not user.check_password(password):
            raise forms.ValidationError("Contraseña incorrecta.")
        
        return self.cleaned_data


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
            'propuesta': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'evidencia': forms.FileInput(attrs={'class': 'form-control'})
        }

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
        fields = ['titulo', 'contenido', 'imagen']  # Incluye el campo de imagen
        widgets = {
            'contenido': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Escribe el contenido de la noticia'}),
        }

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
    class Meta:
        model = ActividadVecinal
        fields = ['titulo', 'descripcion', 'fecha', 'hora_inicio', 'hora_fin', 
                 'lugar', 'cupo_maximo', 'imagen', 'precio']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time'}),
            'hora_fin': forms.TimeInput(attrs={'type': 'time'}),
        }