from .models import *
from decimal import Decimal
from django.utils.timezone import now
import openpyxl
from datetime import datetime
import csv
from io import TextIOWrapper

def delete_user_date(request):
    user = request.user
    try:
        # Delete related objects in reverse order of dependency
        NetWorth.objects.filter(user=user).delete()
        #Pension.objects.filter(user=user).delete()
        #Bank.objects.filter(user=user).delete()
        #Investment.objects.filter(broker__user=user).delete()
        #Broker.objects.filter(user=user).delete()
        #FixedCosts.objects.filter(user=user).delete()
        Transaction.objects.filter(user=user).delete()
        #Category.objects.filter(user=user).delete()
        MonthlyExpenses.objects.filter(payday__user=user).delete()
        Payday.objects.filter(user=user).delete()
        #UserPreferences.objects.filter(user=user).delete()

        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

def handle_csv_file(request, csv_file, monthly_expenses):
    csv_reader = csv.DictReader(TextIOWrapper(csv_file.file, encoding='utf-8'))
    try:
        for row in csv_reader:
            transaction_type = row['Transaction Type']
            if transaction_type == 'Purchase':
                date = row['Date']
                time = row['Time']
                description = row['Transaction Description']
                amount = Decimal(row['Amount'])
                combined_note = f"{date} - {time}\n{description}".strip()
                # Create Transaction
                new_transaction = Transaction.objects.create(
                    user=request.user,
                    monthly_expenses=monthly_expenses,
                    amount=abs(amount),
                    note=combined_note
                )
      
        return True
    
    except Exception as e:
                print(f"Error updating everything: {e}")
                return False


def handle_uploaded_file(uploaded_file, request):
    wb = openpyxl.load_workbook(uploaded_file)
    sheet = wb.active
    # Process rows and add data to your database
    for row in sheet.iter_rows(min_row=2, values_only=False):  # Skip the header
        if len(row) == 10:  # Ensure there are exactly 10 columns
            try:
                # Get values from the cells
                from_date = row[0].value
                payday_date = row[1].value
                payday_amount = row[2].value
                networth_amount = row[3].value
                savings_amount = row[4].value
                utilities = row[5].value
                groceries = row[6].value
                misc = row[7].value
                investments_amount = row[8].value
                pension_amount = row[9].value

                # Adjust date format
                from_date = datetime.strptime(str(from_date).split()[0], "%Y-%m-%d")
                payday_date = datetime.strptime(str(payday_date).split()[0], "%Y-%m-%d")
                
                # Extract comment
                networth_note = row[3].comment.text if row[3].comment else ''
                fixedcost_note = row[5].comment.text if row[5].comment else ''
                groceries_note = row[6].comment.text if row[6].comment else ''
                misc_note = row[7].comment.text if row[7].comment else ''
                # Merge the notes
                combined_note = f"{misc_note}\n{fixedcost_note}\n{groceries_note}".strip()

                payday_obj = Payday.objects.create(
                    user=request.user,
                    payday_date=payday_date,
                    amount=payday_amount
                )
                NetWorth.objects.create(
                    user=request.user,
                    payday=payday_obj,
                    date=payday_date,
                    total_savings=savings_amount,
                    total_investments=investments_amount,
                    total_pension=pension_amount,
                    net_worth=networth_amount,
                    note=networth_note
                )
                monthly_expenses = MonthlyExpenses.objects.create(
                    payday=payday_obj,
                    start_date=from_date,
                    end_date=payday_date,
                    utilities=utilities,
                    groceries=groceries,
                    misc=misc,
                    amount=utilities + groceries + misc,
                    note=combined_note
                )
                if not FixedCosts.objects.filter(user=request.user, name='Utilities').exists(): # Creates a category with same name but no ME
                    FixedCosts.objects.create(
                        user=request.user,
                        name='Utilities',
                        amount=0,
                        note='Created after uploading xlsx file'
                    )
                FixedCosts.objects.create(
                    user=request.user,
                    monthly_expenses=monthly_expenses,
                    name='Utilities',
                    amount=utilities,
                    note=fixedcost_note
                )
                Category.objects.create(
                    user=request.user,
                    monthly_expenses=monthly_expenses,
                    name='Groceries',
                    amount=groceries,
                    note=groceries_note
                )
            
            except Exception as e:
                print(f"Error updating everything: {e}")
                return False

        else:
            print(f"Skipping row due to incorrect format: {row}")
            return False

    return True  

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
        print(f"Error creating net_worth: {e}")
        return False  
    
def update_monthly_expenses(request, monthly_expenses, payday):
    try:
        # Check if thare are fixed_costs and utilities related to ME, otherwise set them to 0
        if FixedCosts.objects.filter(user=request.user, monthly_expenses=monthly_expenses).exists():
            monthly_expenses.utilities = monthly_fixed_costs(request, payday.id, monthly_expenses.id)
        else:
            monthly_expenses.utilities = 0
        if Category.objects.filter(user=request.user, monthly_expenses=monthly_expenses, name='Groceries').exists():
            monthly_expenses.groceries = Category.objects.get(user=request.user, monthly_expenses=monthly_expenses, name='Groceries').amount
        else:
            monthly_expenses.groceries = 0
            
        # Get all the categories related to ME except for groceries
        misc_categories = Category.objects.filter(
            user=request.user, 
            monthly_expenses=monthly_expenses
        ).exclude(name='groceries')
        # Calculate the total amount from categories related to ME
        misc_amount = sum(category.amount for category in misc_categories)

        # Get all the transactions related to ME but without a category
        misc_transactions = Transaction.objects.filter(
            user=request.user, 
            monthly_expenses=monthly_expenses,
            category__isnull=True)
        # Calculate the total amount from misc_transactions
        transactions_without_category = sum(transaction.amount for transaction in misc_transactions)

        # Update misc
        monthly_expenses.misc = misc_amount + transactions_without_category

        # Update total amount
        monthly_expenses.amount = (
            monthly_expenses.utilities 
            + monthly_expenses.groceries 
            + monthly_expenses.misc
        ) - monthly_expenses.deductions

        monthly_expenses.save()
        return True

    except Exception as e:
        print(f"Error updating monthly expenses: {e}")
        return False

def search_payday(request, search_type, *args):
    if search_type == 'note':
        # Search by note content
        note = args[0]  # The first argument is the note
        paydays = Payday.objects.filter(
            note__icontains=note  # Search for paydays with a note containing the search text
        )
        return paydays

    elif search_type == 'date':
        # Search by month and year
        month_str = args[0]  # The first argument is the month (string, e.g. 'January')
        year_str = args[1]  # The second argument is the year (string, e.g. '2025')

        # Convert month string to a number (e.g. 'January' -> 1)
        try:
            month_number = datetime.strptime(month_str, "%B").month  # %B for full month name (e.g. 'January')
        except ValueError:
            # In case the month is invalid or not recognized
            return None

        # Convert year_str to an integer
        try:
            year = int(year_str)
        except ValueError:
            # If the year is invalid
            return None

        # Filter paydays based on the converted month and year
        paydays = Payday.objects.filter(
            payday_date__month=month_number,  # Month as integer
            payday_date__year=year  # Year as integer
        )
        return paydays

    else:
        return None  # Return None if no valid search type is provided
    
def search_net_worth(request, search_type, *args):
    if search_type == 'note':
        # Search by note content
        note = args[0]  # The first argument is the note
        net_worths = NetWorth.objects.filter(
            note__icontains=note  # Search for paydays with a note containing the search text
        )
        return net_worths

    elif search_type == 'date':
        # Search by month and year
        month_number = args[0]  # The first argument is the month (string, e.g. 'January')
        year_str = args[1]  # The second argument is the year (string, e.g. '2025')
        # Convert year_str to an integer
        try:
            year = int(year_str)
        except ValueError:
            # If the year is invalid
            return False
        # Filter paydays based on the converted month and year
        net_worths = NetWorth.objects.filter(
            date__month=month_number,  # Month as integer
            date__year=year  # Year as integer
        )
        return net_worths

    else:
        return False  # Return False if no valid search type is provided

def check_user_investment(request, investment_id): # Check if an investment is related to the current user
        user_brokers = Broker.objects.filter(user=request.user)
        for broker in user_brokers:
            if Investment.objects.filter(broker=broker, id=investment_id).exists():
                return Investment.objects.get(broker=broker, id=investment_id)
        return None