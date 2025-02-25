from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class TravelerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='traveler_profile')

    # additional fields
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    interests = models.TextField(null=True, blank=True)
    acessibility_needs = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s profile."
