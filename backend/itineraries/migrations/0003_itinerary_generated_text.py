# Generated by Django 5.1.6 on 2025-02-14 11:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('itineraries', '0002_itinerary_lat_itinerary_lng_review'),
    ]

    operations = [
        migrations.AddField(
            model_name='itinerary',
            name='generated_text',
            field=models.TextField(blank=True, null=True),
        ),
    ]
