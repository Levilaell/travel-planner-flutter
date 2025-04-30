# forms.py

from django import forms
from django.conf import settings

from .models import Day, Itinerary, Review


class ItineraryForm(forms.ModelForm):
    class Meta:
        model = Itinerary
        fields = [
            'destination',
            'start_date',
            'end_date',
            'budget',
            'travelers',
            'extras',
        ]

    def clean(self):
        cleaned = super().clean()
        start  = cleaned.get("start_date")
        end    = cleaned.get("end_date")

        if start and end and (end - start).days + 1 > settings.MAX_ITINERARY_DAYS:
            raise forms.ValidationError(
                (f"Maximum itinerary length is {settings.MAX_ITINERARY_DAYS} days.")
            )
        if end and start and end < start:
            raise forms.ValidationError(("End date must be after start date."))

        return cleaned


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
