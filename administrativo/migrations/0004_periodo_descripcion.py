# Generated by Django 4.2 on 2023-04-21 14:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrativo', '0003_modeloevaluativo_detallemodeloevaluativo_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='periodo',
            name='descripcion',
            field=models.CharField(default='', max_length=200, verbose_name='Descripción'),
        ),
    ]