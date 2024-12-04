from django.db import models
from django.contrib.auth.models import User

class UserPreferences(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  
    currency_symbol = models.CharField(max_length=5, default='£')  

    def __str__(self):
        return f"Preferences: Currency {self.currency_symbol}"
    
class Rule(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey('Category', null=True, blank=True, on_delete=models.CASCADE)
    fixed_cost = models.ForeignKey('FixedCosts', null=True, blank=True, on_delete=models.CASCADE)
    note = models.TextField(blank=True)

    def __str__(self):
        if self.category:
            return f"Rule for Category: {self.category.name}"
        elif self.fixed_cost:
            return f"Rule for Fixed Cost: {self.fixed_cost.name}"
        return "Unassigned Rule"

class Payday(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='paydays')
    payday_date = models.DateTimeField()
    amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    note = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'payday'

    def get_expenses(self):
        try:
            monthly_expense = MonthlyExpenses.objects.get(payday=self)
            return monthly_expense
        except:
            return None
        
    def get_net_worth(self):
        try:
            net_worth = NetWorth.objects.get(payday=self)
            return net_worth
        except Exception as e:
            print(f"Error fetching related net_worth: {e}")

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
        return f'Name: {self.name}, ME id: , Amount: {self.amount}'
    
    def get_transactions_amount(self):
        try:
            transactions = Transaction.objects.filter(user=self.user, category=self)
            transactions_amount = sum(transaction.amount for transaction in transactions)
            return transactions_amount
        except Exception as e:
            print(f"Error calculating total category amount: {e}")
            return ValueError
    
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
            if previous_category != None:
                return self.amount - previous_category.amount 
        return None
    
    def times_used(self):
        all_categories = Category.objects.filter(user=self.user, name=self.name, monthly_expenses__isnull=False)
        return len(all_categories)

    def average_amount(self):
        try:
            all_categories = Category.objects.filter(user=self.user, name=self.name, monthly_expenses__isnull=False)
            category_average_amount = sum(category.amount for category in all_categories) / len(all_categories)
            return category_average_amount
        except:
            return 0
    
    def latest(self):
        try:
            latest_category = Category.objects.filter(user=self.user, name=self.name, monthly_expenses__isnull=False).order_by('-monthly_expenses__payday__payday_date').first()
            return latest_category.amount
        except:
            return 0

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    monthly_expenses = models.ForeignKey(MonthlyExpenses, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    note = models.CharField(max_length=255, null=True, blank=True)

    def delete_transaction(self):
        try:
            if self.category:
                self.category.amount -= self.amount
                self.category.save()
            self.delete()
        except Exception as e:
            print(f"Error deleting transaction: {e}")

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
        return f"{self.name}: ({self.amount}, {self.monthly_expenses.id})"
    
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
            if previous_fixed_cost != None:
                return self.amount - previous_fixed_cost.amount 
        return None
    
    def times_used(self):
        all_fixed_costs = FixedCosts.objects.filter(user=self.user, name=self.name, monthly_expenses__isnull=False)
        return len(all_fixed_costs)

    def average_amount(self):
        try:
            all_fixed_costs = FixedCosts.objects.filter(user=self.user, name=self.name, monthly_expenses__isnull=False)
            fixed_cost_average_amount = sum(fixed_cost.amount for fixed_cost in all_fixed_costs) / len(all_fixed_costs)
            return fixed_cost_average_amount
        except:
            return 0
        
    def latest(self):
        try:
            latest_fixed_cost = FixedCosts.objects.filter(user=self.user, name=self.name).order_by('-monthly_expenses__payday__payday_date').first()
            return latest_fixed_cost.amount
        except:
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
        return f'Net Worth for {self.user.username} on {self.date} for {self.net_worth}'
    
    def perc_diff_with_last_month(self):
        previous_net_worth = (
            NetWorth.objects.filter(user=self.user, date__lt=self.date)
            .order_by('-date')
            .first()
        )
        if previous_net_worth and previous_net_worth.net_worth:
            try:
                difference = self.net_worth - previous_net_worth.net_worth
                percentage_change = (difference / previous_net_worth.net_worth) * 100
                return round(percentage_change, 2) 
            except ZeroDivisionError:
                return 0  # Handle case where the previous net worth is zero
        return 0  # Return None if no previous record exists
    
    def perc_diff_investments(self):
        previous_net_worth = (
            NetWorth.objects.filter(user=self.user, date__lt=self.date)
            .order_by('-date')
            .first()
        )
        try:
            difference = self.total_investments - previous_net_worth.total_investments
            percentage_change = (difference / previous_net_worth.total_investments) * 100
            return round(percentage_change, 2) 
        except Exception as e:
            print(f"Error perc_diff_investments: {e}")
            return 0
        
    def perc_diff_pensions(self):
        previous_net_worth = (
            NetWorth.objects.filter(user=self.user, date__lt=self.date)
            .order_by('-date')
            .first()
        )
        try:
            difference = self.total_pension - previous_net_worth.total_pension
            percentage_change = (difference / previous_net_worth.total_pension) * 100
            return round(percentage_change, 2) 
        except Exception as e:
            print(f"Error perc_diff_pensions: {e}")
            return 0
        
    def perc_diff_savings(self):
        previous_savings = (
            NetWorth.objects.filter(user=self.user, date__lt=self.date)
            .order_by('-date')
            .first()
        )
        try:
            difference = self.total_savings - previous_savings.total_savings
            percentage_change = (difference / previous_savings.total_savings) * 100
            return round(percentage_change, 2) 
        except Exception as e:
            print(f"Error perc_diff_savings: {e}")
            return 0
