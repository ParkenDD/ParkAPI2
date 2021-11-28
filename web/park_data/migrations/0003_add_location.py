# Generated by Django 3.2.9 on 2021-11-27 13:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('locations', '0001_initial'),
        ('park_data', '0002_add_latest_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='parkinglot',
            name='location',
            field=models.ForeignKey(blank=True, help_text='A link to a location description', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='parking_lots', to='locations.location', verbose_name='Location'),
        ),
        migrations.AlterField(
            model_name='parkinglot',
            name='latest_data',
            field=models.OneToOneField(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, to='park_data.latestparkingdata', verbose_name='Latest data'),
        ),
    ]