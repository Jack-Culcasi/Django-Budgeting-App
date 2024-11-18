from .models import *
from decimal import Decimal
from django.utils.timezone import now

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
    
def create_and_update_fixed_cost(request, new_amounts, fixed_cost_ids, monthly_expenses):
    try:
        # Create a list of tuples containg (id, amount)
        amount_ids_list = [] # [(1, 500), (2,300)]
        for x in range(0, len(new_amounts)):
            amount_ids_list.append((int(fixed_cost_ids[x]), Decimal(new_amounts[x])))

        # Create a new fixed_costs object related to the monthly expenses
        for element in amount_ids_list:
            fixed_cost = FixedCosts.objects.get(user=request.user, id=element[0])
            new_fixed_costs = FixedCosts.objects.create(
                user=request.user,
                monthly_expenses=monthly_expenses,
                name = fixed_cost.name,
                amount=element[1]                
                )
            # Update Fixed Cost record without ME 
            fixed_cost.amount = element[1] 
            fixed_cost.save()

        return True
    
    except Exception as e:
        # Log the exception if needed
        print(f"Error updating or creating fixed_cost: {e}")
        return False  
    
def get_total_savings(request):
    user_banks = Bank.objects.filter(user=request.user)
    total_savings = 0
    for bank in user_banks:
        total_savings += bank.amount
    return Decimal(total_savings)

def get_total_investments(request):
    user_investments = Investment.objects.filter(broker__user=request.user)
    total_investments = 0
    for investment in user_investments:
        total_investments += investment.amount
    return Decimal(total_investments)

def get_total_pensions(request):
    user_pensions = Pension.objects.filter(user=request.user)
    total_pension = 0
    for pension in user_pensions:
        total_pension += pension.amount
    return Decimal(total_pension)

def create_net_worth(request, payday):
    try:
        total_savings = get_total_savings(request)
        total_investments = get_total_investments(request)
        total_pensions = get_total_pensions(request)
        net_worth_amount = total_investments + total_pensions + total_savings

        net_worth = NetWorth.objects.create(
            user=request.user,
            payday=payday,
            date=now(),  # Current timestamp
            total_savings=total_savings,
            total_investments=total_investments,
            total_pension=total_pensions,
            net_worth=net_worth_amount
        )
        return True
    
    except Exception as e:
        # Log the exception if needed
        print(f"Error creating net_worth: {e}")
        return False  
    
def update_monthly_expenses(request, monthly_expenses, payday):
    try:
        monthly_expenses.utilities = monthly_fixed_costs(request, payday.id, monthly_expenses.id)
        monthly_expenses.groceries = Category.objects.get(user=request.user, monthly_expenses=monthly_expenses, name='Groceries').amount 
        
        # Get all the categories related to ME except for groceries 
        misc_categories = Category.objects.filter(
            user=request.user, 
            monthly_expenses=monthly_expenses
        ).exclude(name='groceries')

        # Calculate the total amount from categories
        misc_amount = sum(category.amount for category in misc_categories)

        # Get all the transactions without category
        misc_transactions = Transaction.objects.filter(
            user=request.user, 
            monthly_expenses=monthly_expenses,
            category__isnull=True
            )
        
        # Calculate the total amount from misc_transactions
        transactions_without_category = sum(transaction.amount for transaction in misc_transactions)

        monthly_expenses.misc = misc_amount
        monthly_expenses.amount = (monthly_expenses.utilities + monthly_expenses.groceries + transactions_without_category) - monthly_expenses.deductions
        monthly_expenses.save()
        print(f"Utilities: {monthly_expenses.utilities}, Groceries: {monthly_expenses.groceries}, "
                f"Misc Amount: {misc_amount}, Transactions Without Category: {transactions_without_category}, "
                f"Total Amount: {monthly_expenses.amount}")
        return True
    
    except Exception as e:
        # Log the exception if needed
        print(f"Error updating monthly expenses: {e}")
        return False      
