# models.py

from django.db import models
from django.contrib.auth.models import User

class Itinerary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    destination = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    travelers = models.PositiveIntegerField(null=True)
    interests = models.TextField(null=True, blank=True)
    food_preferences = models.CharField(max_length=50, null=True)
    extras = models.TextField(max_length=200, null=True)
    transport_mode = models.CharField(max_length=20, null=True)
    interest_places = models.TextField(max_length=200, null=True, blank=True)
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Texto geral gerado pela IA (overview)
    generated_text = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Roteiro de {self.user.username} - {self.destination}'

    @property
    def total_days(self):
        """Quantidade de dias entre start_date e end_date (inclusivo)."""
        return (self.end_date - self.start_date).days + 1


class Day(models.Model):
    """
    Representa um dia específico dentro do Itinerary.
    """
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name='days')
    day_number = models.PositiveIntegerField()
    date = models.DateField()
    
    # Texto gerado pela IA para este dia
    generated_text = models.TextField(null=True, blank=True)

    # Opcional: campo para armazenar lista (parseada) das atrações visitadas
    places_visited = models.TextField(null=True, blank=True)  
    # Ex: "Basílica de Sacré-Cœur, Place du Tertre, Museu do Louvre, ..."

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
