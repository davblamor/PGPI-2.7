# Generated by Django 5.1.3 on 2024-11-19 18:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='session_id',
            field=models.CharField(blank=True, max_length=255, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='order',
            name='track_number',
            field=models.CharField(blank=True, max_length=255, null=True, unique=True),
        ),
    ]