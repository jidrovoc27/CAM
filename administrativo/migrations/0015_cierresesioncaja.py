# Generated by Django 4.2 on 2023-04-24 21:38

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('administrativo', '0014_pago_sesioncaja'),
    ]

    operations = [
        migrations.CreateModel(
            name='CierreSesionCaja',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True, verbose_name='Fecha creación')),
                ('fecha_modificacion', models.DateTimeField(auto_now=True, verbose_name='Fecha Modificación')),
                ('status', models.BooleanField(default=True, verbose_name='Estado del registro')),
                ('fechacierre', models.DateField(verbose_name='Fecha fin')),
                ('totalfacturado', models.DecimalField(decimal_places=2, default=0, max_digits=30, verbose_name='Valor con el que cierra la caja')),
                ('sesioncaja', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='administrativo.sesioncaja', verbose_name='Sesión caja')),
                ('usuario_creacion', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='Usuario Creación')),
                ('usuario_modificacion', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='Usuario Modificación')),
            ],
            options={
                'verbose_name': 'Cierre Sesion Caja',
                'verbose_name_plural': 'Cierres de sesiones de caja',
                'ordering': ['id'],
            },
        ),
    ]