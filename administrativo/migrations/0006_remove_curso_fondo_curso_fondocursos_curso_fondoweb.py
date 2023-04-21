# Generated by Django 4.2 on 2023-04-21 19:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrativo', '0005_alter_curso_options_curso_costoinscripcion_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='curso',
            name='fondo',
        ),
        migrations.AddField(
            model_name='curso',
            name='fondocursos',
            field=models.ImageField(blank=True, null=True, upload_to='fondocursos', verbose_name='Fondo para cursos'),
        ),
        migrations.AddField(
            model_name='curso',
            name='fondoweb',
            field=models.ImageField(blank=True, null=True, upload_to='fondoweb', verbose_name='Fondo para página web'),
        ),
    ]
