from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from .models import TravelerProfile

@receiver(post_save, sender=User)
def create_user_profile_and_token(sender, instance, created, **kwargs):
    if created:
        TravelerProfile.objects.create(user=instance)
        Token.objects.create(user=instance)
        