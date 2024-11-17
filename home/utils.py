from .models import *
from decimal import Decimal

def monthly_variable_costs(request, payday_id, monthly_expense_id):
    payday = Payday.objects.get(user=request.user, id=payday_id)
    monthly_expenses = MonthlyExpenses.objects.get(payday=payday, id=monthly_expense_id)
    transactions = Transaction.objects.filter(user=request.user, monthly_expenses=monthly_expenses)

    variable_costs = 0
    for transaction in transactions:
        variable_costs += transaction.amount
    
    return variable_costs

def monthly_fixed_costs(request, payday_id, monthly_expense_id):
    payday = Payday.objects.get(user=request.user, id=payday_id)
    monthly_expenses = MonthlyExpenses.objects.get(payday=payday, id=monthly_expense_id)
    fixed_costs = FixedCosts.objects.filter(user=request.user, monthly_expenses=monthly_expenses)

    monthly_fixed_costs = 0
    for fixed_cost in fixed_costs:
        monthly_fixed_costs += fixed_cost.amount
    
    return monthly_fixed_costs

def get_deductions(full_amounts, split_fixed_costs, deduction_amount):
    deductions = 0
    deductions += float(deduction_amount)
    for amount in full_amounts:
        deductions += float(amount)
    for amount in split_fixed_costs:
        deductions += float(amount) / 2
    return Decimal(deductions)