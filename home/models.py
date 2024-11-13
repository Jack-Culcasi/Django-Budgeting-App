from django.db import models
from django.contrib.auth.models import User

class UserPreferences(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  
    currency_symbol = models.CharField(max_length=5, default='£')  

    def __str__(self):
        return f"Preferences: Currency {self.currency_symbol}"

class Payday(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='paydays')
    payday_date = models.DateTimeField()
    amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    note = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'payday'

    def __str__(self):
        return f'Payday for {self.user.username} on {self.payday_date}'

class MonthlyExpenses(models.Model):
    payday = models.ForeignKey(Payday, on_delete=models.CASCADE, related_name='monthly_expenses')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    utilities = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    groceries = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    misc = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    note = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'monthly_expenses'

    def __str__(self):
        return f'Monthly Expenses for {self.payday}'
    
class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    monthly_expenses = models.ForeignKey(MonthlyExpenses, on_delete=models.CASCADE, related_name='categories', null=True, blank=True)
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    note = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    monthly_expenses = models.ForeignKey(MonthlyExpenses, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    note = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.category.name} - {self.amount} by {self.user.username}"
    
class FixedCosts(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  
    monthly_expenses = models.ForeignKey(MonthlyExpenses, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)  
    amount = models.DecimalField(max_digits=15, decimal_places=2)  
    note = models.CharField(max_length=255, null=True, blank=True)  

    def __str__(self):
        return f"{self.name}: ({self.amount}, {self.monthly_expenses})"

class Broker(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='brokers')
    name = models.CharField(max_length=64)
    amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    latest_update = models.DateTimeField(auto_now=True)
    note = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'broker'

    def __str__(self):
        return f'Broker: {self.name} for {self.user.username}'

class Investment(models.Model):
    broker = models.ForeignKey(Broker, on_delete=models.CASCADE, related_name='investments')
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    note = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Investment in {self.name} for {self.amount} by {self.broker.name}"


class Bank(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='banks')
    name = models.CharField(max_length=64)
    amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    latest_update = models.DateTimeField(auto_now=True)
    note = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'bank'

    def __str__(self):
        return f'Bank: {self.name} for {self.user.username}'


class Pension(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pensions')
    name = models.CharField(max_length=64)
    amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    latest_update = models.DateTimeField(auto_now=True)
    note = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'pension'

    def __str__(self):
        return f'Pension: {self.name} for {self.user.username}'


class NetWorth(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='net_worths')
    payday = models.ForeignKey(Payday, on_delete=models.CASCADE, related_name='net_worths')
    date = models.DateTimeField()
    total_savings = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    total_investments = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    total_pension = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    net_worth = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    note = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'net_worth'

    def __str__(self):
        return f'Net Worth for {self.user.username} on {self.date}'
