from .models import *
from decimal import Decimal
from django.utils.timezone import now
import openpyxl
from datetime import datetime
import csv
from io import TextIOWrapper

def delete_user_data(request):
    user = request.user
    try:
        # Delete related objects in reverse order of dependency
        NetWorth.objects.filter(user=user).delete()
        Pension.objects.filter(user=user).delete()
        Bank.objects.filter(user=user).delete()
        Investment.objects.filter(broker__user=user).delete()
        Broker.objects.filter(user=user).delete()
        FixedCosts.objects.filter(user=user).delete()
        Transaction.objects.filter(user=user).delete()
        Category.objects.filter(user=user).delete()
        MonthlyExpenses.objects.filter(payday__user=user).delete()
        Payday.objects.filter(user=user).delete()

        # Create a new Groceries category
        Category.objects.create(user=request.user, name='Groceries')

        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

def detect_delimiter(csv_file):
    """
    Reads a few lines of the CSV file and detects whether it uses ',' or '\t' as a delimiter.
    """
    sample = csv_file.file.read(1024).decode("utf-8")  # Read a small part of the file
    csv_file.file.seek(0)  # Reset file pointer after reading

    if "\t" in sample and "," not in sample:
        return "\t"  # File uses tabs
    else:
        return ","  # Default to commas

def handle_csv_file(request, csv_file, monthly_expenses):
    delimiter = detect_delimiter(csv_file)  # Auto-detect delimiter
    csv_reader = csv.DictReader(TextIOWrapper(csv_file.file, encoding='utf-8'), delimiter=delimiter)
    try:
        # Fetch all rules for the current user
        rules = Rule.objects.filter(user=request.user)
        # Get the user's custom preferences if they exist
        preferences = getattr(request.user, 'csv_preferences', None)

        for row in csv_reader:
            if row.get('Transaction Type'):
                transaction_type = row['Transaction Type']
                
            else:
                # Use preferences if available, otherwise set to 'Purchase' so that it triggers next if condition
                transaction_type = row[preferences.transaction_type] if preferences and preferences.transaction_type else 'Purchase'

            if 'Purchase' in transaction_type or 'Direct Debit' in transaction_type:
                date = row[preferences.date] if preferences and preferences.date else row.get('Date')
                time = row[preferences.time] if preferences and preferences.time else row.get('Time')
                
                if time == None:
                    time = ''

                description = row[preferences.transaction_description] if preferences and preferences.transaction_description else row.get('Transaction Description')
                amount = Decimal(row[preferences.amount] if preferences and preferences.amount else row.get('Amount'))

                # If the amount of the transaction is 0 the whole row is skipped.
                if amount == 0:
                    continue
                
                combined_note = f"{date} - {time}\n{description}".strip()

                # Initialize category or fixed cost as None
                matched_category = None
                matched_fixed_cost = None

                # Apply rules by matching against the rule's note
                for rule in rules:
                    if rule.note and rule.note.lower() in description.lower():
                        if rule.category:
                            matched_category = rule.category
                        elif rule.fixed_cost:
                            matched_fixed_cost = rule.fixed_cost

                            # Check if a Fixed Cost with the same name already exists
                            existing_fixed_cost = FixedCosts.objects.filter(
                                user=request.user,
                                monthly_expenses=monthly_expenses,
                                name=matched_fixed_cost.name
                            ).first()

                            if existing_fixed_cost:
                                # If it exists, update the Fixed Cost but do NOT add to Monthly Expenses again
                                existing_fixed_cost.amount += abs(amount)
                                existing_fixed_cost.save()
                            else:
                                # If it doesn't exist, create a new Fixed Cost
                                FixedCosts.objects.create(
                                    user=request.user,
                                    monthly_expenses=monthly_expenses,
                                    name=matched_fixed_cost.name,
                                    amount=abs(amount)
                                )

                            # Since this transaction is already counted as a Fixed Cost, we SKIP creating it separately
                            break  # Stop checking once a match is found

                else:  
                    # Only create a transaction if it was NOT marked as a Fixed Cost
                    Transaction.objects.create(
                        user=request.user,
                        monthly_expenses=monthly_expenses,
                        amount=abs(amount),
                        note=combined_note,
                        category=matched_category
                    )

        return True

    except Exception as e:
        print(f"Error processing CSV: {e}")
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

def adjust_fixedcosts_categories(request, full_cost_values, split_cost_values):
        # This function directly subtracts full and split deductions from the objects
        # Initialize containers for selected objects
        full_fixed_costs = []
        split_fixed_costs = []
        full_categories = []
        split_categories = []
        try:
            # Process full-cost checkboxes
            for value in full_cost_values:
                object_type, object_id = value.split('-')  # Extract type and ID (i.e. fixedcost-{{ fixed_cost.id }} )
                object_id = int(object_id)

                if object_type == "fixedcost":
                    # Fetch and append the FixedCost object
                    full_fixed_costs.append(FixedCosts.objects.get(user=request.user, id=object_id))
                elif object_type == "category":
                    # Fetch and append the Category object
                    full_categories.append(Category.objects.get(user=request.user, id=object_id))

            # Process split-cost checkboxes (same logic as above)
            for value in split_cost_values:
                object_type, object_id = value.split('-')
                object_id = int(object_id)

                if object_type == "fixedcost":
                    split_fixed_costs.append(FixedCosts.objects.get(user=request.user, id=object_id))
                elif object_type == "category":
                    split_categories.append(Category.objects.get(user=request.user, id=object_id))

            for full_fixed_cost in full_fixed_costs:
                full_fixed_cost.amount = 0
                full_fixed_cost.save()
            for split_fixed_cost in split_fixed_costs:
                split_fixed_cost.amount /= 2
                split_fixed_cost.save()

            for full_category in full_categories:
                full_category.amount = 0
                full_category.save()
            for split_category in split_categories:
                split_category.amount /= 2
                split_category.save()

            return True            
            
        except Exception as e:
            print(f"Error adjust_fixedcosts_categories: {e}")
            return False  

        

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
            # Check if the fixed cost already exists within the ME (because added when uploading the transactions file)
            if fixed_cost.monthly_expenses == None:
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

        if monthly_expenses.amount == None:
            monthly_expenses.amount = 0

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
    user = request.user  # Get the logged-in user

    if search_type == 'note':
        note = args[0].strip()  # The note content to search for
        result_set = set()

        # Filter by user in all queries
        paydays = Payday.objects.filter(user=user, note__icontains=note)
        result_set.update(paydays)

        net_worths = NetWorth.objects.filter(user=user, note__icontains=note)
        for net_worth in net_worths:
            if net_worth.payday:
                result_set.add(net_worth.payday)

        monthly_expenses = MonthlyExpenses.objects.filter(payday__user=user, note__icontains=note)
        for expense in monthly_expenses:
            if expense.payday:
                result_set.add(expense.payday)

        return list(result_set)

    elif search_type == 'date':
        try:
            month_number = datetime.strptime(args[0], "%B").month
            year = int(args[1])
        except ValueError:
            return None

        paydays = Payday.objects.filter(
            user=user,
            payday_date__month=month_number,
            payday_date__year=year
        )
        return paydays

    return None
    
def search_net_worth(request, search_type, *args):
    user = request.user  # Get the logged-in user

    if search_type == 'note':
        note = args[0].strip()

        net_worths_qs = NetWorth.objects.filter(user=user, note__icontains=note)
        paydays_qs = Payday.objects.filter(user=user, note__icontains=note)
        net_worths_from_paydays_qs = NetWorth.objects.filter(user=user, payday__in=paydays_qs)

        monthly_expenses_qs = MonthlyExpenses.objects.filter(payday__user=user, note__icontains=note)
        net_worths_from_expenses_qs = NetWorth.objects.filter(
            user=user, payday__in=monthly_expenses_qs.values_list('payday', flat=True)
        )

        all_net_worths = net_worths_qs.union(net_worths_from_paydays_qs, net_worths_from_expenses_qs)
        return all_net_worths

    elif search_type == 'date':
        try:
            month_number = int(args[0])  # Already expected as integer
            year = int(args[1])
        except ValueError:
            return False

        net_worths = NetWorth.objects.filter(
            user=user,
            date__month=month_number,
            date__year=year
        )
        return net_worths

    return False


def check_user_investment(request, investment_id): # Check if an investment is related to the current user
        user_brokers = Broker.objects.filter(user=request.user)
        for broker in user_brokers:
            if Investment.objects.filter(broker=broker, id=investment_id).exists():
                return Investment.objects.get(broker=broker, id=investment_id)
        return None

def from_to_net_worths(request, from_month, from_year, to_month, to_year):
    user = request.user  # Get the logged-in user

    # Construct start and end datetime objects
    start_date = datetime(year=int(from_year), month=int(from_month), day=1)
    end_date = datetime(year=int(to_year), month=int(to_month), day=1)

    # Adjust end_date to include the entire "To" month
    if end_date.month == 12:
        end_date = datetime(year=end_date.year + 1, month=1, day=1)
    else:
        end_date = datetime(year=end_date.year, month=end_date.month + 1, day=1)

    # Fetch only the NetWorth objects that belong to the logged-in user
    net_worth_objects = NetWorth.objects.filter(
        user=user,  # Filters by logged-in user
        date__gte=start_date,
        date__lt=end_date
    )

    return net_worth_objects