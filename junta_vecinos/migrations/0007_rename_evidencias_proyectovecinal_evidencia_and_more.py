# Generated by Django 5.1 on 2024-10-06 16:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('junta_vecinos', '0006_remove_proyectovecinal_archivo_propuesta_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='proyectovecinal',
            old_name='evidencias',
            new_name='evidencia',
        ),
        migrations.RenameField(
            model_name='proyectovecinal',
            old_name='titulo',
            new_name='propuesta',
        ),
    ]