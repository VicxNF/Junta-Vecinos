# Generated by Django 5.1 on 2024-11-19 19:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('junta_vecinos', '0024_administradorcomuna_presidente_apellidos_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='administradorcomuna',
            name='firma_presidente',
            field=models.ImageField(blank=True, null=True, upload_to='firmas_presidentes/', verbose_name='Firma del Presidente'),
        ),
    ]