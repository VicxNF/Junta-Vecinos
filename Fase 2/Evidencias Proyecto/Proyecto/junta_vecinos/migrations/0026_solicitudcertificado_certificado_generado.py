# Generated by Django 5.1 on 2024-11-19 21:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('junta_vecinos', '0025_administradorcomuna_firma_presidente'),
    ]

    operations = [
        migrations.AddField(
            model_name='solicitudcertificado',
            name='certificado_generado',
            field=models.FileField(blank=True, null=True, upload_to='certificados/', verbose_name='Certificado de Residencia'),
        ),
    ]