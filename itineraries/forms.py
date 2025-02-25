# forms.py

from django import forms
from .models import Itinerary, Day, Review

class ItineraryForm(forms.ModelForm):
    class Meta:
        model = Itinerary
        fields = [
            'destination',
            'start_date',
            'end_date',
            'budget',
            'travelers',
            'interests',
            'food_preferences',
            'extras',
            'transport_mode',
            'interest_places',
        ]

class DayForm(forms.ModelForm):
    class Meta:
        model = Day
        fields = ['day_number', 'date', 'generated_text']
        # Em muitos casos, day_number e date podem ser calculados automaticamente,
        # mas caso deseje permitir edição manual, mantenha-os.

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
