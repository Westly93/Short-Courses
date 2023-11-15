# Generated by Django 4.2.6 on 2023-11-03 07:26

import datetime
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import simple_history.models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0012_proofofpayment_status_alter_profile_dob_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='dob',
            field=models.DateField(blank=True, null=True, validators=[django.core.validators.MaxValueValidator(datetime.date(2007, 11, 7))]),
        ),
        migrations.CreateModel(
            name='HistoricalProofOfPayment',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('date_of_payment', models.DateField()),
                ('bank_from', models.CharField(max_length=255)),
                ('bank_to', models.CharField(max_length=255)),
                ('reference', models.CharField(max_length=255)),
                ('amount', models.CharField(max_length=255)),
                ('payment_method', models.CharField(blank=True, max_length=255, null=True)),
                ('file', models.TextField(max_length=100)),
                ('status', models.CharField(choices=[('Processed', 'Processed'), ('Approved', 'Approved'), ('Pending', 'Pending')], default='Pending', max_length=20)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical proof of payment',
                'verbose_name_plural': 'historical proof of payments',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]