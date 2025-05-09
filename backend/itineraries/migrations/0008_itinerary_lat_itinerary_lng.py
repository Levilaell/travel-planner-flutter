# Generated by Django 5.1.6 on 2025-02-17 15:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('itineraries', '0007_rename_transport_modes_itinerary_transport_mode'),
    ]

    operations = [
        migrations.AddField(
            model_name='itinerary',
            name='lat',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='itinerary',
            name='lng',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
    ]
