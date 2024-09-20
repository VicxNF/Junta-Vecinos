from django import forms
from django.contrib.auth.models import User
from .models import *

class RegistroVecinoForm(forms.ModelForm):
    nombres = forms.CharField(label="Nombres", max_length=255)
    apellidos = forms.CharField(label="Apellidos", max_length=255)
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
    email = forms.EmailField(label="Correo Electrónico")
    fecha_nacimiento = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label="Fecha de Nacimiento")

    class Meta:
        model = Vecino
        fields = ['nombres', 'apellidos', 'direccion', 'telefono', 'fecha_nacimiento']

    def save(self, commit=True):
        email = self.cleaned_data['email']
        password = self.cleaned_data['password']
        nombres = self.cleaned_data['nombres']
        apellidos = self.cleaned_data['apellidos']
        
        # Asegúrate de usar un nombre de usuario único
        username = email.split('@')[0]  # Puedes usar una parte del email como nombre de usuario, por ejemplo
        
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'password': password,
                'email': email,
                'first_name': nombres,
                'last_name': apellidos
            }
        )
        if created:
            user.set_password(password)
            user.save()
        
        vecino = super().save(commit=False)
        vecino.user = user
        vecino.nombres = nombres
        vecino.apellidos = apellidos
        if commit:
            vecino.save()
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
        fields = ['titulo', 'descripcion', 'archivo_propuesta']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Describa su proyecto'}),
        }


class CorreoAprobacionForm(forms.Form):
    contenido = forms.CharField(widget=forms.Textarea(attrs={'rows': 5}), label='Contenido del correo')

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
        fields = ['nombre', 'descripcion', 'capacidad']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control'}),
            'capacidad': forms.NumberInput(attrs={'class': 'form-control'}),
        }