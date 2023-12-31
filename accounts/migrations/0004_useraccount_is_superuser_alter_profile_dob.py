# Generated by Django 4.2.6 on 2023-10-26 08:01

import datetime
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_alter_profile_dob_alter_profile_gender_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='useraccount',
            name='is_superuser',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='profile',
            name='dob',
            field=models.DateField(blank=True, null=True, validators=[django.core.validators.MaxValueValidator(datetime.date(2007, 10, 30))]),
        ),
    ]
