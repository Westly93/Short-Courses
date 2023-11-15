# Generated by Django 4.2.6 on 2023-11-07 08:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0015_alter_historicalproofofpayment_amount_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalproofofpayment',
            name='amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='proofofpayment',
            name='amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
