# Generated by Django 4.2 on 2023-05-03 20:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrativo', '0004_secuencial'),
    ]

    operations = [
        migrations.AddField(
            model_name='pago',
            name='estado',
            field=models.IntegerField(blank=True, choices=[(1, 'VALIDADO'), (2, 'ANULADO')], default=1, null=True, verbose_name='Validado o anulado'),
        ),
        migrations.AddField(
            model_name='pago',
            name='iva',
            field=models.DecimalField(decimal_places=2, default=12, max_digits=30, verbose_name='Iva'),
        ),
        migrations.AddField(
            model_name='pago',
            name='subtotal_iva',
            field=models.FloatField(default=0, verbose_name='Subtotal iva'),
        ),
        migrations.AlterField(
            model_name='factura',
            name='ivaaplicado',
            field=models.IntegerField(blank=True, choices=[(1, 0), (2, 12), (3, 14)], default=2, null=True, verbose_name='Tipo de iva'),
        ),
    ]
