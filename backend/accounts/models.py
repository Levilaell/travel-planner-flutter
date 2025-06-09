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


# Signal handlers for User model
@receiver(post_save, sender=User)
def sync_user_to_firestore(sender, instance, **kwargs):
    """Sync Django User to Firestore."""
    if getattr(settings, 'USE_FIREBASE', False):
        try:
            from firebase_adapter import save_to_firestore_collection
            user_data = {
                'id': instance.id,
                'username': instance.username,
                'email': instance.email,
                'first_name': instance.first_name or '',
                'last_name': instance.last_name or '',
                'date_joined': instance.date_joined.isoformat(),
                'is_active': instance.is_active,
                'is_staff': instance.is_staff,
                'last_login': instance.last_login.isoformat() if instance.last_login else None,
                '_model': 'User',
                '_updated_at': instance.date_joined.isoformat()
            }
            save_to_firestore_collection('users', str(instance.id), user_data)
            print(f"✅ User {instance.username} synced to Firestore")
        except Exception as e:
            print(f"❌ Error syncing user to Firestore: {e}")

@receiver(post_delete, sender=User)
def delete_user_from_firestore(sender, instance, **kwargs):
    """Delete Django User from Firestore."""
    if getattr(settings, 'USE_FIREBASE', False):
        try:
            from firebase_adapter import FirebaseManager
            firebase = FirebaseManager()
            firebase.db.collection('users').document(str(instance.id)).delete()
            print(f"✅ User {instance.username} deleted from Firestore")
        except Exception as e:
            print(f"❌ Error deleting user from Firestore: {e}")

# Connect signals for Firebase synchronization
if getattr(settings, 'USE_FIREBASE', False):
    post_save.connect(sync_to_firestore, sender=TravelerProfile)
    post_delete.connect(delete_from_firestore, sender=TravelerProfile)
