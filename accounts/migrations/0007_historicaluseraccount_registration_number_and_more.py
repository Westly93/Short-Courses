# Generated by Django 4.2.6 on 2023-10-30 09:16

import datetime
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_alter_profile_dob_historicaluseraccount'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicaluseraccount',
            name='registration_number',
            field=models.CharField(blank=True, db_index=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='useraccount',
            name='registration_number',
            field=models.CharField(blank=True, max_length=10, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='dob',
            field=models.DateField(blank=True, null=True, validators=[django.core.validators.MaxValueValidator(datetime.date(2007, 11, 3))]),
        ),
    ]