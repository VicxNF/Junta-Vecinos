# Generated by Django 5.1 on 2024-10-26 23:14

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('junta_vecinos', '0018_remove_solicitudregistrovecino_administrador_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='actividadvecinal',
            name='precio',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10),
        ),
    ]
