# Generated by Django 5.1 on 2024-10-06 17:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('junta_vecinos', '0007_rename_evidencias_proyectovecinal_evidencia_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='proyectovecinal',
            name='evidencia',
            field=models.ImageField(blank=True, null=True, upload_to='evidencias/'),
        ),
    ]