# models.py

from django.contrib.auth.models import User  # type: ignore
from django.db import models  # type: ignore


class Itinerary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    destination = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    travelers = models.PositiveIntegerField(null=True, blank=True)
    interests = models.TextField(null=True, blank=True)
    extras = models.TextField(max_length=200, null=True, blank=True)
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Texto geral gerado pela IA (overview)
    generated_text = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Roteiro de {self.user.username} - {self.destination}'

    @property
    def total_days(self):
        return (self.end_date - self.start_date).days + 1


class Day(models.Model):
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name='days')
    day_number = models.PositiveIntegerField()
    date = models.DateField()
    
    # Texto gerado pela IA para este dia
    generated_text = models.TextField(null=True, blank=True)

    # Aqui armazenamos a lista de locais visitados (serializada em JSON).
    places_visited = models.TextField(null=True, blank=True)
    # Exemplo:
    # [
    #   {"name": "Torre Eiffel", "lat":48.8584, "lng":2.2945},
    #   {"name": "Museu do Louvre", "lat":48.8606, "lng":2.3376}
    # ]

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Dia {self.day_number} ({self.date}) - {self.itinerary.destination}"


class Review(models.Model):
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=0)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review {self.rating} by {self.user.username} on {self.itinerary.destination}"
