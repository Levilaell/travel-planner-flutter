from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from firebase_adapter import FirebaseModelMixin, sync_to_firestore, delete_from_firestore
from django.conf import settings

# Create your models here.
class TravelerProfile(FirebaseModelMixin, models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='traveler_profile')

    # additional fields
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    interests = models.TextField(null=True, blank=True)
    acessibility_needs = models.BooleanField(default=False)
    favorite_destinations = models.JSONField(default=list, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    preferred_language = models.CharField(max_length=10, default='en', choices=[('en', 'English'), ('pt', 'Portuguese')])

    def __str__(self):
        return f"{self.user.username}'s profile."


# Connect signals for Firebase synchronization
if getattr(settings, 'USE_FIREBASE', False):
    post_save.connect(sync_to_firestore, sender=TravelerProfile)
    post_delete.connect(delete_from_firestore, sender=TravelerProfile)
