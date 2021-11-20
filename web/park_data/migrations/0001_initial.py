# Generated by Django 3.2.9 on 2021-11-20 23:33

import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='City',
            fields=[
                ('osm_id', models.CharField(help_text='The ID must be prefixed with N, W or R (for Node, Way or Relation)', max_length=32, primary_key=True, serialize=False, verbose_name='OpenStreetMap ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Date of creation')),
                ('name', models.CharField(db_index=True, max_length=64, null=True, verbose_name='Name')),
                ('geo_point', django.contrib.gis.db.models.fields.PointField(blank=True, db_index=True, null=True, srid=4326, verbose_name='Geographic center')),
                ('geo_polygon', django.contrib.gis.db.models.fields.MultiPolygonField(blank=True, db_index=True, null=True, srid=4326, verbose_name='Geographic outline')),
            ],
            options={
                'verbose_name': 'City',
                'verbose_name_plural': 'Cities',
            },
        ),
        migrations.CreateModel(
            name='Country',
            fields=[
                ('osm_id', models.CharField(help_text='The ID must be prefixed with N, W or R (for Node, Way or Relation)', max_length=32, primary_key=True, serialize=False, verbose_name='OpenStreetMap ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Date of creation')),
                ('name', models.CharField(db_index=True, max_length=64, null=True, verbose_name='Name')),
                ('geo_point', django.contrib.gis.db.models.fields.PointField(blank=True, db_index=True, null=True, srid=4326, verbose_name='Geographic center')),
                ('geo_polygon', django.contrib.gis.db.models.fields.MultiPolygonField(blank=True, db_index=True, null=True, srid=4326, verbose_name='Geographic outline')),
                ('iso_code', models.CharField(db_index=True, help_text='two-letter ISO 3166 country code', max_length=64, unique=True, verbose_name='country code')),
            ],
            options={
                'verbose_name': 'Country',
                'verbose_name_plural': 'Country',
            },
        ),
        migrations.CreateModel(
            name='State',
            fields=[
                ('osm_id', models.CharField(help_text='The ID must be prefixed with N, W or R (for Node, Way or Relation)', max_length=32, primary_key=True, serialize=False, verbose_name='OpenStreetMap ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Date of creation')),
                ('name', models.CharField(db_index=True, max_length=64, null=True, verbose_name='Name')),
                ('geo_point', django.contrib.gis.db.models.fields.PointField(blank=True, db_index=True, null=True, srid=4326, verbose_name='Geographic center')),
                ('geo_polygon', django.contrib.gis.db.models.fields.MultiPolygonField(blank=True, db_index=True, null=True, srid=4326, verbose_name='Geographic outline')),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='states', to='park_data.country', verbose_name='Country')),
            ],
            options={
                'verbose_name': 'State',
                'verbose_name_plural': 'States',
            },
        ),
        migrations.CreateModel(
            name='ParkingLot',
            fields=[
                ('lot_id', models.CharField(help_text='This ID uniquely identifies a single parking lot through all history', max_length=64, primary_key=True, serialize=False, verbose_name='ID of parking lot')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Date of creation')),
                ('osm_id', models.BigIntegerField(null=True, verbose_name='OpenStreetMap ID')),
                ('geo_coords', django.contrib.gis.db.models.fields.PointField(db_index=True, null=True, srid=4326, verbose_name='Location of parking lot')),
                ('geo_polygon', django.contrib.gis.db.models.fields.PolygonField(db_index=True, null=True, srid=4326, verbose_name='Outline of parking lot')),
                ('name', models.CharField(db_index=True, max_length=64, verbose_name='Name of parking lot')),
                ('address', models.TextField(max_length=1024, null=True, verbose_name='Address of parking lot')),
                ('lot_type', models.CharField(db_index=True, help_text="Let's see what base types we can crystalize", max_length=64, null=True, verbose_name='Type of lot')),
                ('max_num_total', models.IntegerField(db_index=True, help_text='The number of maximum total spaces that have been encountered', null=True, verbose_name='Maximum total spaces')),
                ('public_url', models.URLField(max_length=4096, null=True, verbose_name='Public website')),
                ('city', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='parking_lots', to='park_data.city', verbose_name='City')),
            ],
            options={
                'verbose_name': 'Parking lot',
                'verbose_name_plural': 'Parking lots',
            },
        ),
        migrations.AddField(
            model_name='city',
            name='country',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cities', to='park_data.country', verbose_name='Country'),
        ),
        migrations.AddField(
            model_name='city',
            name='state',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cities', to='park_data.state', verbose_name='State'),
        ),
        migrations.CreateModel(
            name='ParkingData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(db_index=True, verbose_name='Date of snapshot')),
                ('status', models.CharField(choices=[('open', 'open'), ('closed', 'closed'), ('unknown', 'unknown'), ('nodata', 'nodata'), ('error', 'error')], db_index=True, max_length=16, verbose_name='State of parking lot (website)')),
                ('num_free', models.IntegerField(db_index=True, null=True, verbose_name='Number of free spaces')),
                ('num_total', models.IntegerField(db_index=True, null=True, verbose_name='Number of total available spaces')),
                ('num_occupied', models.IntegerField(db_index=True, null=True, verbose_name='Number of occupied spaces')),
                ('percent_free', models.FloatField(db_index=True, null=True, verbose_name='Free spaces in percent')),
                ('lot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='park_data.parkinglot', verbose_name='Parking lot')),
            ],
            options={
                'verbose_name': 'Parking data',
                'verbose_name_plural': 'Parking data',
                'unique_together': {('timestamp', 'lot')},
            },
        ),
    ]
