# Generated by Django 5.1.3 on 2024-11-26 19:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0006_alter_order_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('Pendiente', 'Pendiente'), ('En proceso', 'En proceso'), ('Enviado', 'Enviado'), ('Entregado', 'Entregado'), ('Cancelado', 'Cancelado')], default='Pendiente', max_length=20),
        ),
    ]
