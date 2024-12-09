from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Category, UserPreferences

@receiver(post_save, sender=User)
def create_groceries_category(sender, instance, created, **kwargs):
    if created:  # Only create the category if the user is new
        # Create the Groceries category for the new user
        Category.objects.create(
            user=instance,  
            name='Groceries',
            note='I have to eat after all' 
        )
        # Create UserPreferences instance
        UserPreferences.objects.create(
            user=instance,
        )