# Generated by Django 5.1 on 2024-10-06 19:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('junta_vecinos', '0007_solicitudregistrovecino'),
    ]

    operations = [
        migrations.AddField(
            model_name='espacio',
            name='foto',
            field=models.ImageField(blank=True, null=True, upload_to='espacios/'),
        ),
        migrations.AddField(
            model_name='espacio',
            name='ubicacion',
            field=models.CharField(default='Ubicación no disponible', max_length=200),
        ),
    ]
