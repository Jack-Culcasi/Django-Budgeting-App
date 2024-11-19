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
    deductions = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    note = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'monthly_expenses'

    def __str__(self):
        return (f"Monthly Expenses [Payday ID: {self.payday.id}, ID: {self.id}, \n"
                f"Start Date: {self.start_date}, End Date: {self.end_date}, \n"
                f"Utilities: {self.utilities}, Groceries: {self.groceries}, \n"
                f"Misc: {self.misc}, Amount: {self.amount}, \n"
                f"Deductions: {self.deductions}, Note: {self.note}]")
    
class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    monthly_expenses = models.ForeignKey(MonthlyExpenses, on_delete=models.CASCADE, related_name='categories', null=True, blank=True)
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    note = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f'Name: {self.name}, ME id: {self.monthly_expenses.id}, Amount: {self.amount}'
    
    def difference_with_last_month(self):
        # Find the previous month's expenses
        last_month_expenses = MonthlyExpenses.objects.filter(
            payday__user=self.user,
            payday__payday_date__lt=self.monthly_expenses.payday.payday_date
        ).order_by('-payday__payday_date').first()
        
        # If previous month exists, find the category there
        if last_month_expenses:
            previous_category = Category.objects.filter(
                user=self.user,
                name=self.name,
                monthly_expenses=last_month_expenses
            ).first()
            return self.amount - (previous_category.amount if previous_category else 0)
        return 0

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    monthly_expenses = models.ForeignKey(MonthlyExpenses, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    note = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        category_name = self.category.name if self.category else "No Category"
        return f"{category_name} - {self.amount} by {self.user.username}"
    
class FixedCosts(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  
    monthly_expenses = models.ForeignKey(MonthlyExpenses, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)  
    amount = models.DecimalField(max_digits=15, decimal_places=2)  
    note = models.CharField(max_length=255, null=True, blank=True)  

    def __str__(self):
        return f"{self.name}: ({self.amount}, {self.monthly_expenses})"
    
    def difference_with_last_month(self):
        # Find the previous month's expenses
        last_month_expenses = MonthlyExpenses.objects.filter(
            payday__user=self.user,
            payday__payday_date__lt=self.monthly_expenses.payday.payday_date
        ).order_by('-payday__payday_date').first()
        
        # If previous month exists, find the category there
        if last_month_expenses:
            previous_fixed_cost = FixedCosts.objects.filter(
                user=self.user,
                name=self.name,
                monthly_expenses=last_month_expenses
            ).first()
            return self.amount - (previous_fixed_cost.amount if previous_fixed_cost else 0)
        return 0

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
