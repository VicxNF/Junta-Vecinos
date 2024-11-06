from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Vecino

@receiver(post_save, sender=User)
def create_vecino(sender, instance, created, **kwargs):
    if created:
        # Puedes omitir la creación del Vecino para usuarios creados desde el superusuario,
        # o proporcionar valores predeterminados adecuados.
        # Aquí se está creando un Vecino solo si se proporciona fecha_nacimiento.
        if hasattr(instance, 'vecino'):
            # No creamos un vecino si ya existe uno asociado
            return
        # Solo crear un Vecino si se han proporcionado todos los datos necesarios
        # Por ejemplo, si 'fecha_nacimiento' tiene un valor predeterminado o si se obtiene de alguna otra manera.
        # vecino = Vecino.objects.create(user=instance, fecha_nacimiento=some_default_value)
