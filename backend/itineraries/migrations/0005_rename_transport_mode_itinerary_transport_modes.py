# Generated by Django 5.1.6 on 2025-02-17 12:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('itineraries', '0004_remove_itinerary_lat_remove_itinerary_lng_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='itinerary',
            old_name='transport_mode',
            new_name='transport_modes',
        ),
    ]
