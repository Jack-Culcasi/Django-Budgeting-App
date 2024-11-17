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

def update_investments(request, new_amounts, investment_ids, broker_ids):
    try:
        # Create a list of lists containing [investment_id, new_amount, broker_id]
        investments_data = [] # [ [1, 200, 1], [2, 100, 2] ]
        for x in range(len(new_amounts)):
            investments_data.append([
                int(investment_ids[x]),
                Decimal(new_amounts[x]),
                int(broker_ids[x]),
            ])

        # Update bank record for every id
        for element in investments_data:
            broker = Broker.objects.get(user=request.user, id=element[2])
            investment = Investment.objects.get(broker=broker, id=element[0])
            investment.amount = element[1] 
            investment.save()

        return True    
    
    except Exception as e:
        # Log the exception if needed
        print(f"Error updating investments: {e}")
        return False  
    
def update_pensions(request, new_amounts, pension_ids):
    try:
        # Create a list of tuples containg (id, amount)
        amount_ids_list = [] # [(1, 500), (2,300)]
        for x in range(0, len(new_amounts)):
            amount_ids_list.append((int(pension_ids[x]), Decimal(new_amounts[x])))
        
        # Update pension record
        for element in amount_ids_list:
            pension = Pension.objects.get(user=request.user, id=element[0])
            pension.amount = element[1] 
            pension.save()

        return True    
    
    except Exception as e:
        # Log the exception if needed
        print(f"Error updating pension: {e}")
        return False  
    
def update_savings(request, new_amounts, bank_ids):
    try:
        # Create a list of tuples containg (id, amount)
        amount_ids_list = [] # [(1, 500), (2,300)]
        for x in range(0, len(new_amounts)):
            amount_ids_list.append((int(bank_ids[x]), Decimal(new_amounts[x])))

        # Update pension record
        for element in amount_ids_list:
            bank = Bank.objects.get(user=request.user, id=element[0])
            bank.amount = element[1] 
            bank.save()

        return True    
    
    except Exception as e:
        # Log the exception if needed
        print(f"Error updating pension: {e}")
        return False  