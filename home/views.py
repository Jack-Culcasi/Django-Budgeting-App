from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.db.models import Count
from datetime import datetime, timedelta
from .models import *
from .utils import *
from decimal import Decimal
from django.db.models import Sum, Max, Min
from .forms import UploadFileForm, CSVUploadForm
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from .forms import CustomUserCreationForm
from django.shortcuts import get_object_or_404
from itertools import chain

def guide(request):
    context = {}
    return render(request, 'guide.html', context)

def statistics(request):
    paydays = Payday.objects.filter(user=request.user)
    years = sorted(set(payday.payday_date.year for payday in paydays))
    net_worth_objects = []
    # Initialize variables with default values
    from_month = None
    from_year = None
    to_month = None
    to_year = None
    summary_text = ""

    if request.method == 'POST':  # Search button pressed
        from_month = request.POST.get('from_month')  
        from_year = request.POST.get('from_year')
        to_month = request.POST.get('to_month')  
        to_year = request.POST.get('to_year')

        # Fetch net worths from dates
        net_worth_objects = from_to_net_worths(request, from_month, from_year, to_month, to_year)

        # Extract associated monthly expenses
        monthly_expenses = MonthlyExpenses.objects.filter(
            payday__in=net_worth_objects.values_list('payday', flat=True)
        )
        total_expenses = sum(exp.amount for exp in monthly_expenses if exp.amount)
        num_months = monthly_expenses.count()
        month_avg = (total_expenses / num_months) if num_months else Decimal(0)

        # Aggregate income data
        total_income = Payday.objects.filter(
            id__in=net_worth_objects.values_list('payday', flat=True)
        ).aggregate(total_income=Sum('amount'))['total_income'] or Decimal(0)

        # Savings rate
        savings_rate = ((total_income - total_expenses) / total_income * 100) if total_income else Decimal(0)

        # Find highest and lowest spending months with their IDs
        highest_spending_month_obj = monthly_expenses.order_by('-amount').first()
        lowest_spending_month_obj = monthly_expenses.order_by('amount').first()

        highest_spending_month = {
            "amount": highest_spending_month_obj.amount if highest_spending_month_obj else "N/A",
            "id": highest_spending_month_obj.payday.id if highest_spending_month_obj else None,
        }

        lowest_spending_month = {
            "amount": lowest_spending_month_obj.amount if lowest_spending_month_obj else "N/A",
            "id": lowest_spending_month_obj.payday.id if lowest_spending_month_obj else None,
        }

        # Category-wise breakdown
        categories = Category.objects.filter(
            monthly_expenses__in=monthly_expenses
        ).values('name').annotate(total_amount=Sum('amount'))


        category_stats = ", ".join(
            f"{cat['name']}: {request.user.userpreferences.currency_symbol} {cat['total_amount']}" 
            for cat in categories
        )

        # Fun facts
        biggest_spending_category = categories.order_by('-total_amount').first()
        fun_fact = ""
        if biggest_spending_category:
            fun_fact = (
                f"Your biggest spending category was '{biggest_spending_category['name']}' "
                f"with a total of {request.user.userpreferences.currency_symbol} {biggest_spending_category['total_amount']}!"
            )

        # Net worth trends
        if net_worth_objects.exists():
            net_worth_start = net_worth_objects.first().net_worth
            net_worth_end = net_worth_objects.last().net_worth
            net_worth_change = net_worth_end - net_worth_start
            net_worth_trend = (
                f"Your net worth {'increased' if net_worth_change > 0 else 'decreased'} by "
                f"{request.user.userpreferences.currency_symbol} {abs(net_worth_change)} during this period."
            )
        else:
            net_worth_trend = "Net worth data is unavailable for this period."

        # Generate summary text
        summary_text = {
            "total_income": f"{total_income}",
            "total_expenses": f"{total_expenses}",
            "month_avg": f"{month_avg:.2f}",
            "savings_rate": f"{savings_rate:.2f}%",
            "highest_spending_month": highest_spending_month,
            "lowest_spending_month": lowest_spending_month,
            "category_breakdown": category_stats,
            "fun_fact": fun_fact,
            "net_worth_trend": net_worth_trend,
        }

    context = {
        'years': years,
        'net_worth_objects': net_worth_objects,
        'summary_text': summary_text,
        'currency': request.user.userpreferences.currency_symbol,
        'from_month': from_month,
        'from_year': from_year,
        'to_month': to_month,
        'to_year': to_year,
    }

    return render(request, 'statistics.html', context)


def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your account has been created! You can now log in.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'signup.html', {'form': form})

@login_required
def settings(request):
    categories = Category.objects.filter(user=request.user, monthly_expenses__isnull=True)
    fixed_costs = FixedCosts.objects.filter(user=request.user, monthly_expenses__isnull=True)
    rules = Rule.objects.filter(user=request.user)
    investments = Investment.objects.filter(broker__user=request.user)
    user_pref = UserPreferences.objects.get(user=request.user)

    if user_pref.main_investment == None:
        try:
            first_investment = Investment.objects.filter(broker__user=request.user).first()
            user_pref.main_investment = first_investment
            user_pref.save()
        except:
            pass

    if request.method == 'POST':

        if 'delete_data' in request.POST:
            if delete_user_data(request):
                messages.success(request, "Your data has been deleted successfully.")
            else:
                messages.error(request, "An error occurred while deleting your data. Please try again.")

        if 'delete_user' in request.POST:
            try:
                user = request.user  
                user.delete()
                messages.success(request, "Your account has been deleted successfully.")                
                return redirect('login')  
            except Exception as e:
                messages.error(request, f"An error occurred while deleting the account: {str(e)}")
                return redirect('home') 

        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data['file']
            if handle_uploaded_file(uploaded_file, request):
                messages.success(request, "Your data has been uploaded successfully.")
            else:
                messages.error(request, "An error occurred while uploading your data. Check if the layout of the file is correct.")
        
        if 'add_rule' in request.POST:
            chosen_option = request.POST.get('choose_option')
            note = request.POST.get('note')

            if chosen_option:
                # Split the value into type and ID
                option_type, option_id = chosen_option.split('-')
                option_id = int(option_id)

                if option_type == 'category':
                    category = Category.objects.get(user=request.user, id=option_id)
                    Rule.objects.create(
                        user=request.user,
                        category=category,
                        note=note
                    )
                elif option_type == 'fixedcost':
                    fixed_cost = FixedCosts.objects.get(user=request.user, id=option_id)
                    Rule.objects.create(
                        user=request.user,
                        fixed_cost=fixed_cost,
                        note=note
                    )
        
        if 'delete_rule' in request.POST:
            rule_id = request.POST.get('delete_rule')
            rule = Rule.objects.get(user=request.user, id=rule_id)
            rule.delete()

        if 'currency_symbol' in request.POST:
            currency_symbol = request.POST.get('currency_symbol')
            user_pref.currency_symbol = currency_symbol
            user_pref.save()

        if 'main_investment' in request.POST:
            main_investment_id = request.POST.get('main_investment')
            main_investment = check_user_investment(request, main_investment_id)
            user_pref.main_investment = main_investment
            user_pref.save()       

        if 'transaction_type' in request.POST:    
            transaction_type = request.POST.get('transaction_type')
            date = request.POST.get('date')
            time = request.POST.get('time')
            transaction_description = request.POST.get('transaction_description')
            amount = request.POST.get('amount')
            try:
                if CsvPreferences.objects.filter(user=request.user).exists():
                    # Amend existing preferences
                    csv_preferences = CsvPreferences.objects.get(user=request.user)
                    csv_preferences.transaction_type = transaction_type
                    csv_preferences.date = date
                    csv_preferences.time = time
                    csv_preferences.transaction_description = transaction_description
                    csv_preferences.amount = amount
                    csv_preferences.save()
                else:    
                    # Create CsvPreferences object
                    csv_preferences = CsvPreferences.objects.create(
                        user=request.user,
                        transaction_type=transaction_type,
                        date=date,
                        time=time,
                        transaction_description=transaction_description,
                        amount=amount
                    )

                messages.success(request, "Your preferences have been uploaded successfully.")

            except Exception as e:
                messages.error(request, f"An error occurred while creating csv preferences: {e}")
                print(f"An error occurred while creating csv_preferences: {e}")
            
    else:
        form = UploadFileForm()
    
    context = {
        'categories': categories,
        'fixed_costs': fixed_costs, 
        'form': form,
        'rules': rules,
        'investments': investments
    }

    return render(request, 'settings.html', context)

@login_required
def home(request):
    # Determine to show the completion bar 
    payday_exists = request.user.paydays.exists() 
    # Determine completion based on existing data for each step
    steps_completed = {
        "account_created": True,
        "add_bank": request.user.banks.exists(),
        "add_broker": request.user.brokers.exists(),
        "add_fixed_cost": request.user.fixedcosts_set.exists(),
        "add_investment": request.user.brokers.filter(investments__isnull=False).exists(),
        "add_categories": request.user.category_set.exclude(name="Groceries").exists(),
    }
    # If payday/networth record
    if NetWorth.objects.filter(user=request.user).exists():
        results = True
        transactions = Transaction.objects.filter(user=request.user)
        monthly_expenses = MonthlyExpenses.objects.filter(payday__user=request.user)
        paydays = Payday.objects.filter(user=request.user)
        user_preferences = UserPreferences.objects.filter(user=request.user)
        categories = Category.objects.filter(user=request.user)
        fixed_costs = FixedCosts.objects.filter(user=request.user)
        brokers = Broker.objects.filter(user=request.user)
        banks = Bank.objects.filter(user=request.user)
        pensions = Pension.objects.filter(user=request.user)
        last_net_worth = NetWorth.objects.filter(user=request.user).order_by('-date').first()
        investments = Investment.objects.filter(broker__user=request.user)
        pac = UserPreferences.objects.get(user=request.user).main_investment
        # Data for graph
        net_worths = NetWorth.objects.filter(user=request.user).order_by('date')  # Order by date
        # Extract dates and net worth values for chart
        dates = [net_worth.date.strftime('%m-%Y') for net_worth in net_worths]
        net_worth_values = [net_worth.net_worth for net_worth in net_worths]
        # Extract total_savings for chart
        savings_values = [net_worth.total_savings for net_worth in net_worths]
        # Extract total_investments for chart
        investments_values = [net_worth.total_investments for net_worth in net_worths]
        # Extract expenses for chart
        expenses_values = [net_worth.payday.get_expenses().amount for net_worth in net_worths]
        # Extract investments excluding PAC
        investments_no_pac = last_net_worth.total_investments - (pac.amount if pac else 0)
        # net worth notes
        net_worth_notes = [net_worth.note for net_worth in net_worths]
        # Monthly expenses notes
        monthly_expenses_notes = [monthly_expense.note for monthly_expense in monthly_expenses]
        # Years for search field
        years = sorted(set(payday.payday_date.year for payday in paydays))

        graph_data = {
            'dates': dates,
            'net_worth_values': net_worth_values,
            'savings_values': savings_values,
            'investments_values': investments_values,
            'expenses_values':expenses_values,
            'savings': last_net_worth.total_savings,
            'investments': investments_no_pac ,
            'pensions': last_net_worth.total_pension,
            'pac': pac.amount if pac else 0,
            'pac_name': pac.name if pac else '',
            'net_worth_notes': net_worth_notes,
            'monthly_expenses_notes': monthly_expenses_notes
        }

        if request.method == 'POST': # Search button pressed
            month = request.POST.get('month')  # Month from dropdown
            year = request.POST.get('year')  # Year from dropdown
            note = request.POST.get('note')  # Note text input
            if note:
                search_type = 'note'
                search_result = search_net_worth(request, search_type, note)
                if search_result:
                    net_worths = search_result
                else:
                    results = False
            else:
                search_type = 'date'
                search_result = search_net_worth(request, search_type, month, year) 
                if search_result:
                    net_worths = search_result
                else:
                    results = False

        context = {
        'last_net_worth': last_net_worth,
        'transactions': transactions,
        'paydays': paydays,
        'monthly_expenses': monthly_expenses,
        'user_preferences': user_preferences,
        'categories': categories,
        'fixed_costs': fixed_costs,
        'brokers': brokers,
        'banks': banks,
        'pensions': pensions,
        'investments': investments,
        'total_investments': get_total_investments(request),
        'total_pensions': get_total_pensions(request),
        'payday_exists': payday_exists,
        'pac': pac,
        'graph_data': graph_data,
        'net_worths': net_worths.order_by('-date')[:9], # Only latest 9 result for table element PROBLEM
        'results': results,
        'years': years
        }   
    else:
        context = {
            'steps_completed': steps_completed,
            'payday_exists': payday_exists,
        }

    return render(request, 'home.html', context)

@login_required
def payday(request):
    today_date = timezone.now().date().strftime('%Y-%m-%d')
    # Check if is first payday ever, if it is, prompt start date field
    try:
        last_two_paydays = Payday.objects.filter(user=request.user).order_by('-payday_date')[:2]
            
    except IndexError: # Not enough paydays to create MonthlyExpenses
        last_two_paydays = None
    
    if request.method == 'POST':
        print(last_two_paydays)
        print(not last_two_paydays)
        # Get the form data
        amount = Decimal(request.POST.get('amount'))
        payday_date = request.POST.get('date')
        start_date = request.POST.get('start_date', None)
        note = request.POST.get('note', None)
        payday_date = timezone.make_aware(datetime.strptime(payday_date, '%Y-%m-%d'))        
        # Create the Payday object
        payday = Payday.objects.create(
            user=request.user,
            payday_date=payday_date,
            amount=amount,
            note=note
        )
        # If first time payday the start_date is taken from the form, otherwise from last_two_paydays[1]
        if not last_two_paydays:
            print('not last_two_paydays')
            monthly_expense = MonthlyExpenses.objects.create(
            payday=payday,
            start_date=start_date,
            end_date=payday_date - timedelta(days=1)
            )
        else:
            print('else')
            last_two_paydays = Payday.objects.filter(user=request.user).order_by('-payday_date')[:2]
            # Create the MonthlyExpenses object for the previous month, 
            # the start date is related to the payday date of the previous month, the end date is the last payday date minus one day.
            # If you are paid every 1st of the month you want your monthly expenses be calculated from the 1st to the 31st.
            monthly_expense = MonthlyExpenses.objects.create(
                payday=payday,
                start_date=last_two_paydays[1].payday_date,
                end_date=payday_date - timedelta(days=1)
                )
        return redirect('expenses', payday_id=payday.id, monthly_expense_id=monthly_expense.id)

    context = {
        'today_date': today_date,
        'last_two_paydays': last_two_paydays,
    }

    return render(request, 'payday.html', context)

@login_required
def expenses(request, payday_id=None, monthly_expense_id=None):
    # Redirect to payday if accessed directly without a payday_id or monthly_expense_id
    if payday_id is None or monthly_expense_id is None:
        return redirect('payday')

    try:
        payday = Payday.objects.get(id=payday_id, user=request.user)
    except Payday.DoesNotExist:
        return redirect('payday')
    
    monthly_expenses = MonthlyExpenses.objects.get(id=monthly_expense_id)
    categories = Category.objects.filter(user=request.user, monthly_expenses__isnull=True) # Retrieve only categories note associated with a MonthlyExpenses object
    transactions = Transaction.objects.filter(user=request.user, monthly_expenses=monthly_expenses)

    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['file']
            if handle_csv_file(request, csv_file, monthly_expenses):
                return redirect('transactions', payday_id, monthly_expense_id)
            else:
                messages.error(request, "There's been a problem with the upload")

    else:
        form = CSVUploadForm()

    context = {
        'payday': payday,
        'categories': categories,
        'transactions': transactions,
        'monthly_expense_id': monthly_expense_id,
        'form': form
    }
    return render(request, 'expenses.html', context)

def transactions(request, payday_id, monthly_expense_id):
    monthly_expenses = MonthlyExpenses.objects.get(id=monthly_expense_id)
    transactions = Transaction.objects.filter(user=request.user, monthly_expenses=monthly_expenses)
    variable_costs = monthly_variable_costs(request, payday_id, monthly_expense_id)
    user_categories = Category.objects.filter(user=request.user, monthly_expenses__isnull=True)
    fixed_costs = FixedCosts.objects.filter(user=request.user, monthly_expenses=monthly_expenses)
    if request.method == 'POST':
        if 'to_fixed_costs' in request.POST:
            # Loop through each transaction to get its selected category
            for transaction in transactions:
                # Get the category ID from the form data for this transaction
                category_id = request.POST.get(f'category_{transaction.id}')

                if category_id: # If category is selected retrieve it and check if it is related to ME
                    category = Category.objects.get(id=category_id)
                    category_exists = Category.objects.filter(
                    user=request.user,
                    name=category.name,
                    monthly_expenses=monthly_expenses
                    ).exists()
                    # If the transaction already has a category and that category has the same name of the selected category 
                    if transaction.category and transaction.category.name == category.name and transaction.category.monthly_expenses == monthly_expenses:
                        continue # Skip the transaction

                    if category_exists: 
                        category = Category.objects.get( # Retrieve the existing category, the transaction will be linked to it
                        user=request.user,
                        name=category.name,
                        monthly_expenses=monthly_expenses
                        )
                        category.amount += Decimal(transaction.amount)
                        category.save()
            
                    else:
                        # Create new category associated with monthly_expenses object
                        category = Category.objects.create(
                            user=request.user,
                            monthly_expenses=monthly_expenses,
                            name=category.name,
                            note=category.note,
                            amount=transaction.amount
                        )

                    transaction.category = category
                    transaction.save()

            return redirect('payday_fixed_costs', payday_id, monthly_expense_id)
        else:
            if 'delete_transaction' in request.POST:
                transaction_id = request.POST.get('delete_transaction')
                transaction_object = Transaction.objects.get(id=transaction_id, user=request.user)
                transaction_object.delete_transaction()
    
    context = {
        'transactions': transactions,
        'user_categories': user_categories,
        'variable_costs': variable_costs,
        'payday_id': payday_id,
        'monthly_expense_id': monthly_expense_id,
        'fixed_costs': fixed_costs
    }
    return render(request, 'transactions.html', context)

@login_required
def add_transaction(request):
    # This view create a Transaction object, if the user selects a category the view check if it is related to the MonthlyExpenses object,
    # if it is the view creates a Transaction and then attaches the existing category.
    # If it is not the view creates a new Transaction and Category object realated to it.
    # If the user does not select any category the view then just creates a new Transaction object.
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount'))
        monthly_expense_id = request.POST.get('monthly_expense_id')
        category_id = request.POST.getlist('categories')
        note = request.POST.get('note', '')
        monthly_expenses = MonthlyExpenses.objects.get(id=monthly_expense_id)
        if category_id: # If a category is selected
            category = Category.objects.get(id=int(category_id[0]), user=request.user) # Get the category object from the selection
            category_name = category.name
            # Check if the category is already related with the MonthlyExpenses object 
            category_exists = Category.objects.filter(
                user=request.user,
                name=category_name,
                monthly_expenses=monthly_expenses
            ).exists()
            if category_exists: 
                category = Category.objects.get( # Retrieve the existing category, the transaction will be linked to it
                user=request.user,
                name=category_name,
                monthly_expenses=monthly_expenses
                )
                category.amount += Decimal(amount)
                category.save()
            else:
                # Create new category associated with monthly_expenses object
                category = Category.objects.create(
                    user=request.user,
                    monthly_expenses=monthly_expenses,
                    name=category_name,
                    note=category.note,
                    amount=amount
                )
        else:
            category = None
            category_name = ''
        try:
            transaction = Transaction.objects.create(
                user=request.user,
                monthly_expenses=monthly_expenses,
                amount=amount,
                category=category,
                note=note
            )
        
            # Return success response with the new transaction data
            return JsonResponse({
                'success': True,
                'amount': amount,
                'symbol': request.user.userpreferences.currency_symbol,
                'category_name': category_name,
                'transaction_id': transaction.id,
            })

        except Category.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Category not found'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def delete_transaction(request, payday_id=None, monthly_expense_id=None, transaction_id=None):
    if request.method == 'POST': # Expenses page
        transaction_id = request.POST.get('transaction_id')  
        monthly_expense_id = request.POST.get('monthly_expense_id')
        payday_id = request.POST.get('payday_id')   
        transaction_object = Transaction.objects.get(id=transaction_id, user=request.user)
        transaction_object.delete_transaction()

    return redirect('expenses', payday_id, monthly_expense_id)
        


@login_required
def paydays(request):
    paydays = Payday.objects.filter(user=request.user).order_by('-payday_date')[:12] # Only show last 12 months paydays
    monthly_expenses = MonthlyExpenses.objects.filter(payday__user=request.user)
    # Years for search field
    years = sorted(set(payday.payday_date.year for payday in Payday.objects.filter(user=request.user)))

    if request.method == 'POST':

        if 'payday_id' in request.POST: # Amend button
            payday_id = request.POST.get('payday_id')
            return redirect('amend_payday', payday_id)
        
        month = request.POST.get('month')  # Month from dropdown
        year = request.POST.get('year')  # Year from dropdown
        note = request.POST.get('note')  # Note text input
        if note:
            search_type = 'note'
            paydays = search_payday(request, search_type, note)
        else:
            search_type = 'date'
            paydays = search_payday(request, search_type, month, year)

    context = {
        'paydays': paydays,
        'monthly_expenses': monthly_expenses,
        'years': years
    }

    return render(request, 'paydays.html', context)

@login_required
def amend_payday(request, payday_id):
    payday_obj = Payday.objects.get(user=request.user, id=payday_id)
    monthly_expenses = get_object_or_404(MonthlyExpenses, payday=payday_obj)
    categories = Category.objects.filter(monthly_expenses=monthly_expenses)
    fixed_costs = FixedCosts.objects.filter(monthly_expenses=monthly_expenses)
    transactions = Transaction.objects.filter(monthly_expenses=monthly_expenses)
    monthly_net = monthly_expenses.payday.amount - monthly_expenses.amount
    monthly_expenses.start_date = monthly_expenses.start_date.date()
    monthly_expenses.end_date = monthly_expenses.end_date.date()
    me_start_date = monthly_expenses.start_date.strftime('%Y-%m-%d')
    me_end_date = monthly_expenses.end_date.strftime('%Y-%m-%d')

    if request.method == 'POST':
        try:
            # Update Monthly Expenses fields
            monthly_expenses.start_date = request.POST.get('start_date')
            monthly_expenses.end_date = request.POST.get('end_date')
            payday_obj.amount = Decimal(request.POST.get('salary'))
            payday_obj.note = request.POST.get('payday_note')
            monthly_expenses.deductions = Decimal(request.POST.get('deductions')) 
            monthly_expenses.save()
            payday_obj.save()

            # Update Categories
            for category in categories:
                category.amount = request.POST.get(f'category_{category.id}_amount', category.amount)
                category.note = request.POST.get(f'category_{category.id}_note', category.note)
                category.save()

            # Update Fixed Costs
            for fixed_cost in fixed_costs:
                fixed_cost.amount = request.POST.get(f'fixed_cost_{fixed_cost.id}_amount', fixed_cost.amount)
                fixed_cost.note = request.POST.get(f'fixed_cost_{fixed_cost.id}_note', fixed_cost.note)
                fixed_cost.save()

            # Update Transactions
            for transaction in transactions:
                transaction.amount = request.POST.get(f'transaction_{transaction.id}_amount', transaction.amount)
                transaction.note = request.POST.get(f'transaction_{transaction.id}_note', transaction.note)
                transaction.save()
                if transaction.category:
                    transaction.category.amount = transaction.category.get_transactions_amount()                    
                    transaction.category.save()

            update_me = update_monthly_expenses(request, monthly_expenses, payday_obj)
            if not update_me:  # If update_me is False, raise an exception
                raise ValueError("Failed to update monthly expenses.")
            
            messages.success(request, "Payday successfully amended")
            return redirect('monthly_expenses', payday_obj.id)
        
        except Exception as e:
            print(f"Error updating monthly expenses: {e}")
            messages.error(request, "An error occurred while amending your Payday. Please try again.")
            

    context = {
        'payday_id': payday_id,
        'payday_obj': payday_obj,
        'monthly_expenses': monthly_expenses,
        'categories': categories,
        'fixed_costs': fixed_costs,
        'transactions': transactions,
        'monthly_net': monthly_net,
        'me_start_date': me_start_date,
        'me_end_date': me_end_date

    }

    return render(request, 'amend_payday.html', context)

@login_required
def delete_payday(request):
    if request.method == 'POST':
        # The Delete button is pressed
        payday_id = request.POST.get('payday_id')
        source = request.POST.get('source', '/home/')
        payday_object = Payday.objects.get(id=payday_id, user=request.user)
        payday_object.delete()

    return redirect(source)

@login_required
def monthly_expenses(request, payday_id):
    payday_object = Payday.objects.get(id=payday_id, user=request.user)
    net_worth = NetWorth.objects.get(user=request.user, payday=payday_object)
    monthly_expenses = MonthlyExpenses.objects.get(payday=payday_object)
    transactions = Transaction.objects.filter(monthly_expenses=monthly_expenses, user=request.user)
    # Add .transactions_count to category object
    categories = Category.objects.filter(user=request.user, monthly_expenses=monthly_expenses).annotate(transactions_count=Count('transaction')) 
    fixed_costs = FixedCosts.objects.filter(user=request.user, monthly_expenses=monthly_expenses)
    monthly_net = monthly_expenses.payday.amount - monthly_expenses.amount
    monthly_expenses.start_date = monthly_expenses.start_date.date()
    monthly_expenses.end_date = monthly_expenses.end_date.date()

    # Notes collapse-content
    notes = {}

    if payday_object.note:
        notes['Payday'] = payday_object.note
    
    if net_worth.note:
        notes['NetWorth'] = net_worth.note
    
    if monthly_expenses.note:
        notes['MonthlyExpenses'] = monthly_expenses.note


    context = {
        'transactions' : transactions,
        'monthly_expenses': monthly_expenses,
        'categories': categories,
        'fixed_costs': fixed_costs,
        'monthly_net': monthly_net,
        'notes': notes
    }

    return render(request, 'monthly_expenses.html', context)

@login_required
def categories(request):
    categories = Category.objects.filter(user=request.user, monthly_expenses__isnull=True)

    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        if category_id: # Delete button
            category_name = Category.objects.get(user=request.user, id=category_id).name
            categories_to_be_deleted = Category.objects.filter(user=request.user, name=category_name)
            for category in categories_to_be_deleted:
                try:
                    category.delete()
                    messages.success(request, "Category successfully deleted.")
                except PermissionDenied:
                    messages.error(request, "You cannot delete this category.")
                    return redirect('categories')
        else: # Add category
            category_name = request.POST.get('name')
            category_note = request.POST.get('note', None)
            new_category = Category.objects.create(
                user=request.user,
                name=category_name,
                note=category_note
            )

    context = {
        'categories': categories
    }
    return render(request, 'categories.html', context)

@login_required
def payday_fixed_costs(request, payday_id, monthly_expense_id):
    payday = Payday.objects.get(user=request.user, id=payday_id)
    monthly_expenses = MonthlyExpenses.objects.get(payday=payday, id=monthly_expense_id)
    variable_costs = monthly_variable_costs(request, payday_id, monthly_expense_id)
    # Retrieve Fixed Costs related to the current Monthly Expenses
    me_fixed_costs = FixedCosts.objects.filter(user=request.user, monthly_expenses=monthly_expenses)
    # Retrieve Fixed Costs not related to any Monthly Expenses
    user_fixed_costs = FixedCosts.objects.filter(user=request.user, monthly_expenses__isnull=True)
    # Filter out user_fixed_costs with names that already exist in me_fixed_costs
    user_fixed_costs_filtered = user_fixed_costs.exclude(name__in=me_fixed_costs.values_list('name', flat=True))
    # Combine the two querysets
    final_fixed_costs = chain(me_fixed_costs, user_fixed_costs_filtered)
    

    if request.method == 'POST':
        new_amounts = request.POST.getlist('new_amount') # [500, 300]
        fixed_cost_ids = request.POST.getlist('fixed_cost_id') # [1, 2]
        
        if fixed_cost_ids: # Post request comes from payday_fixed_costs.html

            # Create or update new FixedCosts object using fixed_cost_ids and new_amounts and update the general object without ME
            if create_and_update_fixed_cost(request, new_amounts, fixed_cost_ids, monthly_expenses):
                return redirect('deductions', payday_id=payday_id, monthly_expense_id=monthly_expense_id)

    context = {
        'final_fixed_costs': final_fixed_costs,
        'payday': payday,
        'variable_costs': variable_costs,
        'monthly_expense_id': monthly_expense_id,
    }
    return render(request, 'payday_fixed_costs.html', context)

@login_required
def fixed_costs(request):
    fixed_costs = FixedCosts.objects.filter(user=request.user, monthly_expenses__isnull=True)

    if request.method == 'POST':
        fixed_cost_id = request.POST.get('fixed_cost_id')
        if fixed_cost_id: # Delete button
            fixed_cost_name = FixedCosts.objects.get(user=request.user, id=fixed_cost_id).name
            fixed_cost_to_be_deleted = FixedCosts.objects.filter(user=request.user, name=fixed_cost_name)
            for fixed_cost in fixed_cost_to_be_deleted:
                fixed_cost.delete()
        else: # Add category
            fixed_cost_name = request.POST.get('name')
            fixed_cost_amount = Decimal(request.POST.get('amount'))
            fixed_cost_note = request.POST.get('note', None)
            new_fixed_cost = FixedCosts.objects.create(
                user=request.user,
                name=fixed_cost_name,
                amount=fixed_cost_amount,
                note=fixed_cost_note
            )

    context = {
        'fixed_costs': fixed_costs
    }
    return render(request, 'fixed_costs.html', context)

@login_required
def deductions(request, payday_id, monthly_expense_id):
    payday = Payday.objects.get(user=request.user, id=payday_id)
    monthly_expenses = MonthlyExpenses.objects.get(payday=payday, id=monthly_expense_id)
    categories = Category.objects.filter(user=request.user, monthly_expenses=monthly_expenses)
    fixed_costs = FixedCosts.objects.filter(user=request.user, monthly_expenses=monthly_expenses)
    variable_costs = monthly_variable_costs(request, payday_id, monthly_expense_id)
    total_fixed_costs = monthly_fixed_costs(request, payday_id, monthly_expense_id)
    if request.method == 'POST':
        deduction_amount = request.POST.get('deduction_amounts')
        if deduction_amount == '': # If there is no input 
            deduction_amount = 0
        full_amounts = request.POST.getlist('full_cost')
        split_fixed_costs = request.POST.getlist('split_cost')
        # The function retrieves objects from the amounts and subtracts the amount directly from the objects
        if adjust_fixedcosts_categories(request, full_amounts, split_fixed_costs):
            monthly_expenses.deductions += Decimal(deduction_amount)
            monthly_expenses.save()
            return redirect('payday_investments', payday_id=payday.id, monthly_expense_id=monthly_expense_id)

    context = {
        'fixed_costs': fixed_costs,
        'categories': categories,
        'payday': payday,
        'monthly_expense_id': monthly_expense_id,
        'variable_costs': variable_costs,
        'total_fixed_costs': total_fixed_costs,
    }
    return render(request, 'deductions.html', context)

@login_required
def payday_investments(request, payday_id, monthly_expense_id):
    payday = Payday.objects.get(user=request.user, id=payday_id)
    monthly_expenses = MonthlyExpenses.objects.get(payday=payday, id=monthly_expense_id)
    variable_costs = monthly_variable_costs(request, payday_id, monthly_expense_id)
    total_fixed_costs = monthly_fixed_costs(request, payday_id, monthly_expense_id)
    investments = Investment.objects.filter(broker__user=request.user)

    if request.method == 'POST': # Update Investment record
        new_amounts = request.POST.getlist('new_amount')
        investment_ids = request.POST.getlist('investment_id')
        broker_ids = request.POST.getlist('broker_id')
        # Update Investment objects using new_amounts, investment_ids and broker_ids
        if update_investments(request, new_amounts, investment_ids, broker_ids):
            return redirect('payday_pension', payday_id=payday.id, monthly_expense_id=monthly_expense_id)
        
    context = {
    'payday': payday,  
    'monthly_expense_id': monthly_expense_id,  
    'variable_costs': variable_costs,  
    'total_fixed_costs': total_fixed_costs,  
    'investments': investments,  
    'deductions': monthly_expenses.deductions,
    }
    return render(request, 'payday_investments.html', context)

@login_required
def payday_pension(request, payday_id, monthly_expense_id):
    user_pensions = Pension.objects.filter(user=request.user)
    payday = Payday.objects.get(user=request.user, id=payday_id)
    monthly_expenses = MonthlyExpenses.objects.get(payday=payday, id=monthly_expense_id)
    variable_costs = monthly_variable_costs(request, payday_id, monthly_expense_id)
    total_fixed_costs = monthly_fixed_costs(request, payday_id, monthly_expense_id)

    if request.method == 'POST': # Update Pension record
        pension_ids = request.POST.getlist('pension_id')
        new_amounts = request.POST.getlist('new_amount')
        if update_pensions(request, new_amounts, pension_ids):
            return redirect('payday_savings', payday_id=payday.id, monthly_expense_id=monthly_expense_id)
        
    
    context = {
        'user_pensions': user_pensions,
        'payday': payday,  
        'monthly_expense_id': monthly_expense_id,  
        'variable_costs': variable_costs,  
        'total_fixed_costs': total_fixed_costs,  
        'deductions': monthly_expenses.deductions,
    }

    return render(request, 'payday_pensions.html', context)

@login_required
def payday_savings(request, payday_id, monthly_expense_id):
    user_banks = Bank.objects.filter(user=request.user)
    payday = Payday.objects.get(user=request.user, id=payday_id)
    monthly_expenses = MonthlyExpenses.objects.get(payday=payday, id=monthly_expense_id)
    variable_costs = monthly_variable_costs(request, payday_id, monthly_expense_id)
    total_fixed_costs = monthly_fixed_costs(request, payday_id, monthly_expense_id)

    if request.method == 'POST': # Update Bank record
        bank_ids = request.POST.getlist('bank_id')
        new_amounts = request.POST.getlist('new_amount')
        updated_savings = update_savings(request, new_amounts, bank_ids)
        if updated_savings:
            # Create the NetWorth object
            if create_net_worth(request, payday) and update_monthly_expenses(request, monthly_expenses, payday):
                return redirect('monthly_expenses', payday_id)
        
    context = {
        'user_banks': user_banks,
        'payday': payday,  
        'monthly_expense_id': monthly_expense_id,  
        'variable_costs': variable_costs,  
        'total_fixed_costs': total_fixed_costs,  
        'deductions': monthly_expenses.deductions,
    }

    return render(request, 'payday_savings.html', context)

@login_required
def banks(request):
    banks = Bank.objects.filter(user=request.user)

    if request.method == 'POST':
        bank_id = request.POST.get('bank_id')
        if bank_id: # Delete button
            bank_to_be_deleted = Bank.objects.get(user=request.user, id=bank_id)
            bank_to_be_deleted.delete()
        else: # Add bank
            bank_name = request.POST.get('name')
            amount = request.POST.get('amount')
            bank_note = request.POST.get('note', None)
            new_bank = Bank.objects.create(
                user=request.user,
                name=bank_name,
                note=bank_note,
                amount=Decimal(amount)
            )

    context = {
        'banks': banks
    }
    return render(request, 'banks.html', context)

@login_required
def investments(request):
    investments = Investment.objects.filter(broker__user=request.user)
    brokers = Broker.objects.filter(user=request.user)

    if request.method == 'POST':
        investment_id = request.POST.get('investment_id')

        if investment_id: # Delete button
            broker_id = request.POST.get('broker_id')
            broker = Broker.objects.get(user=request.user, id=broker_id)
            investment = Investment.objects.get(broker=broker, id=investment_id)
            investment.delete()
            broker.amount -= investment.amount
            broker.save()
        else: # Add an Investment
            investment_name = request.POST.get('name')
            investment_amount = Decimal(request.POST.get('amount'))
            investment_note = request.POST.get('note', None)
            broker_id = request.POST.get('broker_id')
            broker = Broker.objects.get(user=request.user, id=broker_id)
            new_investment = Investment.objects.create(
                name=investment_name,
                amount=investment_amount,
                note=investment_note,
                broker=broker
            )
            broker.amount += investment_amount
            broker.save()

    context = {
        'investments': investments,
        'brokers':brokers,
    }
    return render(request, 'investments.html', context)

@login_required
def brokers(request):
    brokers = Broker.objects.filter(user=request.user)

    if request.method == 'POST':
        broker_id = request.POST.get('broker_id')
        if broker_id: # Delete button
            broker_to_be_deleted = Broker.objects.get(user=request.user, id=broker_id)
            broker_to_be_deleted.delete()
        else: # Add bank
            broker_name = request.POST.get('name')
            broker_note = request.POST.get('note', None)
            new_broker = Broker.objects.create(
                user=request.user,
                name=broker_name,
                note=broker_note,
                amount=Decimal(0)
            )

    context = {
        'brokers': brokers
    }
    return render(request, 'brokers.html', context)

@login_required
def pensions(request):
    pensions = Pension.objects.filter(user=request.user)
    net_worths = NetWorth.objects.filter(user=request.user).order_by('date')  # Order by date
    # Extract dates and pension values for chart
    dates = [net_worth.date.strftime('%m-%Y') for net_worth in net_worths]
    pension_values = [net_worth.total_pension for net_worth in net_worths]
    net_worth_values = [net_worth.net_worth for net_worth in net_worths]

    graph_data = {
        'dates': dates,
        'pension_values': pension_values,
        'net_worth_values': net_worth_values
    }

    if request.method == 'POST':
        pension_id = request.POST.get('pension_id')
        if pension_id: # Delete button
            pension_to_be_deleted = Pension.objects.get(user=request.user, id=pension_id)
            pension_to_be_deleted.delete()
        else: # Add bank
            amount = request.POST.get('amount')
            pension_name = request.POST.get('name')
            pension_note = request.POST.get('note', None)
            new_pension = Pension.objects.create(
                user=request.user,
                name=pension_name,
                note=pension_note,
                amount=amount
            )

    context = {
        'pensions': pensions,
        'graph_data': graph_data
    }
    return render(request, 'pensions.html', context)


@login_required
def category(request, category_name):
    # Charts data
    user_categories = Category.objects.filter(user=request.user, name=category_name).exclude(monthly_expenses__isnull=True)
    categories_notes = [category.note for category in user_categories]
    categories_dates = [category.monthly_expenses.end_date.strftime('%m-%Y') for category in user_categories]
    categories_values = [category.amount for category in user_categories]
    user_monthly_expenses = [category.monthly_expenses for category in user_categories]
    utilities_values = [monthly_expenses.utilities for monthly_expenses in user_monthly_expenses]
    expenses_value = [monthly_expenses.amount for monthly_expenses in user_monthly_expenses]
    expenses_note = [monthly_expenses.note for monthly_expenses in user_monthly_expenses]
    graph_data = {
        'categories_dates': categories_dates,
        'categories_values': categories_values,
        'utilities_values': utilities_values,
        'expenses_value': expenses_value,
        'categories_notes': categories_notes,
        'expenses_note': expenses_note,
        'category_name': category_name
    }



    context = {
        'graph_data': graph_data,
        'user_categories': user_categories,
        'sorted_user_categories': user_categories.order_by('-monthly_expenses__end_date'),
        'category_name': category_name,
    }

    return render(request, 'category.html', context)

@login_required
def fixed_cost(request, fixed_cost_name):
    # Charts data
    user_fixed_costs = FixedCosts.objects.filter(user=request.user, name=fixed_cost_name).exclude(monthly_expenses__isnull=True)
    fixed_cost_notes = [fixed_cost.note for fixed_cost in user_fixed_costs]
    user_fixed_dates = [user_fixed.monthly_expenses.end_date.strftime('%m-%Y') for user_fixed in user_fixed_costs]
    user_fixed_values = [user_fixed.amount for user_fixed in user_fixed_costs]
    user_monthly_expenses = [user_fixed.monthly_expenses for user_fixed in user_fixed_costs]
    utilities_values = [monthly_expenses.utilities for monthly_expenses in user_monthly_expenses]
    expenses_value = [monthly_expenses.amount for monthly_expenses in user_monthly_expenses]
    expenses_note = [monthly_expenses.note for monthly_expenses in user_monthly_expenses]
    graph_data = {
        'user_fixed_dates': user_fixed_dates,
        'user_fixed_values': user_fixed_values,
        'utilities_values': utilities_values,
        'expenses_value': expenses_value,
        'fixed_cost_notes': fixed_cost_notes,
        'expenses_note': expenses_note,
        'fixed_cost_name': fixed_cost_name
    }



    context = {
        'graph_data': graph_data,
        'user_fixed_costs': user_fixed_costs,
        'sorted_user_fixed_costs': user_fixed_costs.order_by('-monthly_expenses__end_date'),
        'category_name': fixed_cost_name,
    }

    return render(request, 'fixed_cost.html', context)

@login_required
def add_note(request):
    if request.method == 'POST':
        object_type = request.POST.get('object_type')  # e.g., 'pension', 'category'
        object_id = request.POST.get('object_id')      
        note = request.POST.get('note', '')

        if not object_type or not object_id:
            return JsonResponse({'success': False, 'error': 'Invalid request data.'})

        # Get the model class dynamically
        try:
            content_type = ContentType.objects.get(model=object_type)
            model_class = content_type.model_class()
            if object_type == 'investment':
                investment = check_user_investment(request, object_id)
                if investment:
                    target_object = investment
            else:
                target_object = get_object_or_404(model_class, id=object_id, user=request.user)
        except ContentType.DoesNotExist:
            return JsonResponse({'success': False, 'error': f'Unknown object type: {object_type}.'})

        # Update the note
        target_object.note = note
        target_object.save()

        return JsonResponse({'success': True, 'note': target_object.note})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})