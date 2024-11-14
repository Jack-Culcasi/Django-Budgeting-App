from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from datetime import datetime, timedelta
from .models import *

@login_required
def home(request):    
    if NetWorth.objects.filter(user=request.user).exists():
        net_worth = NetWorth.objects.filter(user=request.user).latest('date')
    else:
        net_worth = 0  # Handle the case when no record exists

    # Determine completion based on existing data for each step
    steps_completed = {
        "account_created": True,
        "add_bank": request.user.banks.exists(),
        "add_broker": request.user.brokers.exists(),
        "add_fixed_cost": request.user.fixedcosts_set.exists(),
        "add_investment": request.user.brokers.filter(investments__isnull=False).exists(),
        "add_categories": request.user.category_set.exists(),
    }
    payday_exists = request.user.paydays.exists() # Determine to show the completion bar

    # Temporary
    '''Transaction.objects.all().delete()
    MonthlyExpenses.objects.all().delete()
    Payday.objects.all().delete()
    UserPreferences.objects.all().delete()
    Category.objects.all().delete()
    FixedCosts.objects.all().delete()
    Broker.objects.all().delete()
    Bank.objects.all().delete()
    Pension.objects.all().delete()
    NetWorth.objects.all().delete()'''

    transactions = Transaction.objects.all()
    monthly_expenses = MonthlyExpenses.objects.all()
    paydays = Payday.objects.all()
    user_preferences = UserPreferences.objects.all()
    categories = Category.objects.all()
    fixed_costs = FixedCosts.objects.all()
    brokers = Broker.objects.all()
    banks = Bank.objects.all()
    pensions = Pension.objects.all()
    net_worths = NetWorth.objects.all()
    investments = Investment.objects.all()
    #UserPreferences.objects.create(user=request.user, currency_symbol='£')   

    context = {
    'net_worth': net_worths,
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
    'steps_completed': steps_completed,
    'payday_exists': payday_exists,
    }   
    
    return render(request, 'home.html', context)

@login_required
def first_time_buttons(request):
    pass

@login_required
def payday(request):
    today_date = timezone.now().date().strftime('%Y-%m-%d')
    # Check if is first payday ever, if it is, prompt start date field
    try:
        last_two_paydays = Payday.objects.filter(user=request.user).order_by('-payday_date')[:2]
            
    except IndexError: # Not enough paydays to create MonthlyExpenses
        last_two_paydays = None

    if request.method == 'POST':
        # Get the form data
        amount = request.POST.get('amount')
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
        if len(last_two_paydays) < 2:
            monthly_expense = MonthlyExpenses.objects.create(
            payday=payday,
            start_date=start_date,
            end_date=payday_date - timedelta(days=1)
            )
        else:
            last_two_paydays = Payday.objects.filter(user=request.user).order_by('-payday_date')[:2]
            # Create the MonthlyExpenses object for the previous month, 
            # the start date is related to the payday date of the previous month, the end date is the last payday date minus one day.
            # If you are paid every 1st of the month you want your monthly expenses be calculated from the 1st to the 31st.
            monthly_expense = MonthlyExpenses.objects.create(
                payday=last_two_paydays[1],
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

    context = {
        'payday': payday,
        'categories': categories,
        'transactions': transactions,
        'monthly_expense_id': monthly_expense_id,
    }
    return render(request, 'expenses.html', context)

@login_required
def add_transaction(request):
    # This view create a Transaction object, if the user selects a category the view check if it is related to the MonthlyExpenses object,
    # if it is the view creates a Transaction and then attaches the existing category.
    # If it is not the view creates a new Transaction and Category object realated to it.
    # If the user does not select any category the view then just creates a new Transaction object.
    if request.method == 'POST':
        amount = request.POST.get('amount')
        monthly_expense_id = request.POST.get('monthly_expense_id')
        category_id = request.POST.getlist('categories')
        note = request.POST.get('note', '')
        monthly_expenses = MonthlyExpenses.objects.get(id=monthly_expense_id)
        if category_id: # If a category is selected
            category = Category.objects.get(id=int(category_id[0]), user=request.user) # Create the category object from the selection
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
            else:
                # Create new category associated with monthly_expenses object
                category = Category.objects.create(
                    user=request.user,
                    monthly_expenses=monthly_expenses,
                    name=category_name,
                    note=category.note
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
def delete_transaction(request):
    if request.method == 'POST':
        transaction_id = request.POST.get('transaction_id')  
        monthly_expense_id = request.POST.get('monthly_expense_id')
        payday_id = request.POST.get('payday_id')     
        transaction_object = Transaction.objects.get(id=transaction_id, user=request.user)
        transaction_object.delete()

    return redirect('expenses', payday_id, monthly_expense_id)
        


@login_required
def paydays(request):
    paydays = Payday.objects.filter(user=request.user)

    context = {
        'paydays': paydays
    }

    return render(request, 'paydays.html', context)

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
    monthly_expenses = MonthlyExpenses.objects.get(payday=payday_object)
    transactions = Transaction.objects.filter(monthly_expenses=monthly_expenses, user=request.user)
    context = {
        'transactions' : transactions
    }

    return render(request, 'monthly_expenses.html', context)

@login_required
def categories(request):
    categories = Category.objects.filter(user=request.user)

    if request.method == 'POST':
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
    user_fixed_costs = FixedCosts.objects.filter(user=request.user)
    payday = Payday.objects.get(user=request.user, id=payday_id)
    monthly_expenses = MonthlyExpenses.objects.get(payday=payday, id=monthly_expense_id)
    transactions = Transaction.objects.filter(user=request.user, monthly_expenses=monthly_expenses)

    variable_costs = 0
    for transaction in transactions:
        variable_costs += transaction.amount

    if request.method == 'POST':
        new_amount = request.POST.getlist('new_amount')
        fixed_cost_id = request.POST.getlist('fixed_cost_id')
        
        if fixed_cost_id: # Post request comes from expenses.html

            # Create a list of tuples containg (id, amount)
            amount_ids_list = []
            for x in range(0, len(new_amount)):
                amount_ids_list.append((int(fixed_cost_id[x]), float(new_amount[x])))

            # Create a new fixed_costs object related to the monthly expenses
            for element in amount_ids_list:
                fixed_cost = FixedCosts.objects.get(user=request.user, id=element[0])
                new_fixed_costs = FixedCosts.objects.create(
                    user=request.user,
                    monthly_expenses=monthly_expenses,
                    name = fixed_cost.name,
                    amount=element[1]                
            )
            return redirect('deductions', payday_id=payday_id, monthly_expense_id=monthly_expense_id)

    context = {
        'user_fixed_costs': user_fixed_costs,
        'payday': payday,
        'variable_costs': variable_costs,
        'monthly_expense_id': monthly_expense_id,
    }
    print('nonpost')
    return render(request, 'payday_fixed_costs.html', context)

@login_required
def fixed_costs(request):
    fixed_costs = FixedCosts.objects.filter(user=request.user)

    if request.method == 'POST':
        fixed_cost_name = request.POST.get('name')
        fixed_cost_amount = request.POST.get('amount')
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
    categories = Category.objects.filter(user=request.user)
    payday = Payday.objects.get(user=request.user, id=payday_id)
    monthly_expenses = MonthlyExpenses.objects.get(payday=payday, id=monthly_expense_id)
    fixed_costs = FixedCosts.objects.filter(user=request.user, monthly_expenses=monthly_expenses)
    transactions = Transaction.objects.filter(user=request.user, monthly_expenses=monthly_expenses)
    # Calculate the total amount of variable costs (transactions) for this month
    variable_costs = 0
    for transaction in transactions:
        variable_costs += transaction.amount
    # Calculate the total amount of variable costs (transactions) for this month
    total_fixed_costs = 0
    for fixed_cost in fixed_costs:
        total_fixed_costs += fixed_cost.amount

    if request.method == 'POST':
        deduction_amount = request.POST.get('deduction_amounts', 0)
        full_amounts = request.POST.getlist('full_fixed_cost')
        split_fixed_costs = request.POST.getlist('split_fixed_cost')
        # Calculate the amount of deductions
        deductions = 0
        deductions += float(deduction_amount)
        for amount in full_amounts:
            deductions += float(amount)
        for amount in split_fixed_costs:
            deductions += float(amount) / 2

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
def banks(request):
    banks = Bank.objects.filter(user=request.user)

    if request.method == 'POST':
        bank_name = request.POST.get('name')
        bank_note = request.POST.get('note', None)
        new_bank = Bank.objects.create(
            user=request.user,
            name=bank_name,
            note=bank_note
        )

    context = {
        'banks': banks
    }
    return render(request, 'banks.html', context)

@login_required
def investments(request):
    investments = Investment.objects.filter(broker__user=request.user)

    if request.method == 'POST':
        investment_name = request.POST.get('name')
        investment_amount = request.POST.get('amount')
        investment_note = request.POST.get('note', None)
        new_investment = Investment.objects.create(
            user=request.user,
            name=investment_name,
            amount=investment_amount,
            note=investment_note
        )

    context = {
        'investments': investments
    }
    return render(request, 'investments.html', context)

@login_required
def brokers(request):
    brokers = Broker.objects.filter(user=request.user)

    if request.method == 'POST':
        broker_name = request.POST.get('name')
        broker_note = request.POST.get('note', None)
        new_broker = Broker.objects.create(
            user=request.user,
            name=broker_name,
            note=broker_note
        )

    context = {
        'brokers': brokers
    }
    return render(request, 'brokers.html', context)
