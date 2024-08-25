from django import forms
from django.contrib.auth.models import User
from .models import *

class ProyectoForm(forms.ModelForm):
    class Meta:
        model = ProyectoVecinal
        fields = ['titulo', 'descripcion', 'estado', 'resolucion']

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
        user = User.objects.create_user(
            username=self.cleaned_data['email'],  # Usamos el email como nombre de usuario
            password=self.cleaned_data['password'],
            email=self.cleaned_data['email'],
            first_name=self.cleaned_data['nombres'],
            last_name=self.cleaned_data['apellidos']
        )
        vecino = super().save(commit=False)
        vecino.user = user
        vecino.nombres = self.cleaned_data['nombres']
        vecino.apellidos = self.cleaned_data['apellidos']
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