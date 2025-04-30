from rest_framework import serializers
from .models import Itinerary, Day

class DaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Day
        fields = ['id', 'day_number', 'date', 'places_visited', 'generated_text']

class ItinerarySerializer(serializers.ModelSerializer):
    # Remove o source errado e deixa o DRF usar o related_name 'days'
    days = DaySerializer(many=True, read_only=True)

    class Meta:
        model = Itinerary
        fields = [
            'id',
            'destination',
            'start_date',
            'end_date',
            'budget',
            'travelers',
            'interests',
            'extras',
            'generated_text',
            'lat',
            'lng',
            'days',
        ]
