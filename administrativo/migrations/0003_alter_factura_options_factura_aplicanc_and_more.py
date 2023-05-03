# Generated by Django 4.2 on 2023-05-03 17:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('administrativo', '0002_rubro_saldo'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='factura',
            options={'ordering': ['numero'], 'verbose_name': 'Factura', 'verbose_name_plural': 'Facturas'},
        ),
        migrations.AddField(
            model_name='factura',
            name='aplicanc',
            field=models.BooleanField(blank=True, default=False, null=True, verbose_name='Aplica nota de crédito'),
        ),
        migrations.AddField(
            model_name='factura',
            name='autorizacion',
            field=models.TextField(blank=True, null=True, verbose_name='Autorizacion'),
        ),
        migrations.AddField(
            model_name='factura',
            name='autorizada',
            field=models.BooleanField(blank=True, default=False, null=True, verbose_name='Autorizada'),
        ),
        migrations.AddField(
            model_name='factura',
            name='claveacceso',
            field=models.CharField(blank=True, max_length=49, null=True, verbose_name='Clave de Acceso'),
        ),
        migrations.AddField(
            model_name='factura',
            name='direccion',
            field=models.TextField(blank=True, default='', null=True, verbose_name='Dirección'),
        ),
        migrations.AddField(
            model_name='factura',
            name='electronica',
            field=models.BooleanField(blank=True, default=False, null=True, verbose_name='Electrónica'),
        ),
        migrations.AddField(
            model_name='factura',
            name='email',
            field=models.CharField(blank=True, default='', max_length=100, null=True, verbose_name='Email'),
        ),
        migrations.AddField(
            model_name='factura',
            name='enviadacliente',
            field=models.BooleanField(blank=True, default=False, null=True, verbose_name='Enviada por correo'),
        ),
        migrations.AddField(
            model_name='factura',
            name='enviadasri',
            field=models.BooleanField(blank=True, default=False, null=True, verbose_name='Enviada al sri'),
        ),
        migrations.AddField(
            model_name='factura',
            name='estado',
            field=models.IntegerField(blank=True, choices=[(1, 'PENDIENTE'), (2, 'FINALIZADA')], default=1, null=True, verbose_name='Estado de la factura'),
        ),
        migrations.AddField(
            model_name='factura',
            name='falloautorizacionsri',
            field=models.BooleanField(blank=True, default=False, null=True, verbose_name='Fallo de Autorización SRI'),
        ),
        migrations.AddField(
            model_name='factura',
            name='falloenviodasri',
            field=models.BooleanField(blank=True, default=False, null=True, verbose_name='Fallo existente al enviar la factura al sri'),
        ),
        migrations.AddField(
            model_name='factura',
            name='fechaautorizacion',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Fecha autorizacion'),
        ),
        migrations.AddField(
            model_name='factura',
            name='firmada',
            field=models.BooleanField(blank=True, default=False, null=True, verbose_name='Firmada'),
        ),
        migrations.AddField(
            model_name='factura',
            name='identificacion',
            field=models.CharField(blank=True, default='', max_length=20, null=True, verbose_name='Identificación'),
        ),
        migrations.AddField(
            model_name='factura',
            name='ivaaplicado',
            field=models.IntegerField(blank=True, choices=[(1, 0), (2, 12), (3, 14)], default=1, null=True, verbose_name='Tipo de identificación'),
        ),
        migrations.AddField(
            model_name='factura',
            name='mensajeautorizacion',
            field=models.TextField(blank=True, null=True, verbose_name='Mensaje de Autorización'),
        ),
        migrations.AddField(
            model_name='factura',
            name='mensajeenvio',
            field=models.TextField(blank=True, null=True, verbose_name='Mensaje de envio por parte del sri'),
        ),
        migrations.AddField(
            model_name='factura',
            name='nombre',
            field=models.CharField(blank=True, default='', max_length=100, null=True, verbose_name='Nombre'),
        ),
        migrations.AddField(
            model_name='factura',
            name='numero',
            field=models.IntegerField(blank=True, default=0, null=True, verbose_name='Numero'),
        ),
        migrations.AddField(
            model_name='factura',
            name='numerocompleto',
            field=models.CharField(blank=True, default='', max_length=20, null=True, verbose_name='Numero Completo'),
        ),
        migrations.AddField(
            model_name='factura',
            name='observacion',
            field=models.TextField(blank=True, default='', null=True, verbose_name='Observación'),
        ),
        migrations.AddField(
            model_name='factura',
            name='pagada',
            field=models.BooleanField(blank=True, default=True, null=True, verbose_name='Pagada'),
        ),
        migrations.AddField(
            model_name='factura',
            name='sesioncaja',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='administrativo.sesioncaja', verbose_name='Caja'),
        ),
        migrations.AddField(
            model_name='factura',
            name='subtotal_base0',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=30, null=True),
        ),
        migrations.AddField(
            model_name='factura',
            name='subtotal_base_iva',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=30, null=True),
        ),
        migrations.AddField(
            model_name='factura',
            name='telefono',
            field=models.CharField(blank=True, default='', max_length=50, null=True, verbose_name='Telefono'),
        ),
        migrations.AddField(
            model_name='factura',
            name='tipo',
            field=models.IntegerField(blank=True, choices=[(1, 'CEDULA'), (2, 'RUC')], default=1, null=True, verbose_name='Tipo de identificación'),
        ),
        migrations.AddField(
            model_name='factura',
            name='tipoambiente',
            field=models.IntegerField(blank=True, default=1, null=True, verbose_name='Tipo Ambiente'),
        ),
        migrations.AddField(
            model_name='factura',
            name='tipoemision',
            field=models.IntegerField(blank=True, default=1, null=True, verbose_name='Tipo Emision'),
        ),
        migrations.AddField(
            model_name='factura',
            name='total',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=30, null=True),
        ),
        migrations.AddField(
            model_name='factura',
            name='total_descuento',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=30, null=True),
        ),
        migrations.AddField(
            model_name='factura',
            name='total_iva',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=30, null=True),
        ),
        migrations.AddField(
            model_name='factura',
            name='valida',
            field=models.BooleanField(blank=True, default=True, null=True, verbose_name='Valida'),
        ),
        migrations.AddField(
            model_name='factura',
            name='weburl',
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
        migrations.AddField(
            model_name='factura',
            name='xml',
            field=models.TextField(blank=True, null=True, verbose_name='XML'),
        ),
        migrations.AddField(
            model_name='factura',
            name='xmlarchivo',
            field=models.FileField(blank=True, null=True, upload_to='comprobantes/facturas/', verbose_name='XML Archivo'),
        ),
        migrations.AddField(
            model_name='factura',
            name='xmlfirmado',
            field=models.TextField(blank=True, null=True, verbose_name='XML Firmado'),
        ),
        migrations.AddField(
            model_name='factura',
            name='xmlgenerado',
            field=models.BooleanField(blank=True, default=False, null=True, verbose_name='XML Generado'),
        ),
        migrations.AlterField(
            model_name='factura',
            name='fecha',
            field=models.DateField(blank=True, null=True, verbose_name='Fecha'),
        ),
        migrations.AlterUniqueTogether(
            name='factura',
            unique_together={('numero',)},
        ),
        migrations.CreateModel(
            name='DetalleFactura',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True, verbose_name='Fecha creación')),
                ('fecha_modificacion', models.DateTimeField(auto_now=True, verbose_name='Fecha Modificación')),
                ('status', models.BooleanField(default=True, verbose_name='Estado del registro')),
                ('factura', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='administrativo.factura')),
                ('pago', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='administrativo.pago')),
                ('usuario_creacion', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='Usuario Creación')),
                ('usuario_modificacion', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='Usuario Modificación')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RemoveField(
            model_name='factura',
            name='pago',
        ),
    ]