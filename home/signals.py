from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MonthlyExpenses, Category

@receiver(post_save, sender=MonthlyExpenses)
def create_categories_for_first_expense(sender, instance, created, **kwargs):
    if created:  # Only trigger on creation of a new MonthlyExpenses object
        user = instance.payday.user  # Get the user associated with the MonthlyExpenses object
        
        # Check if any MonthlyExpenses exist for this user
        if not MonthlyExpenses.objects.filter(payday__user=user).exists():  # If no other MonthlyExpenses exist
            
            # Create the default categories
            categories = [
                {'name': 'Grocery', 'note': "I have to eat after all"},
                {'name': 'Miscellaneous', 'note': "I have bought a rally car for myself!"}
            ]
            
            for category in categories:
                Category.objects.create(user=user, name=category['name'], note=category['note'])
