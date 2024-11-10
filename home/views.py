from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from datetime import datetime, timedelta
from .models import NetWorth, Payday, Category, Transaction, MonthlyExpenses

@login_required
def home(request):    
    if NetWorth.objects.filter(user=request.user).exists():
        net_worth = NetWorth.objects.filter(user=request.user).latest('date')
    else:
        net_worth = 0  # Handle the case when no record exists
    
    # Temporary
    transactions = Transaction.objects.all()
    monthly_expenses = MonthlyExpenses.objects.all()
    paydays = Payday.objects.all()
    context = {
        'net_worth': net_worth,
        'transactions': transactions,
        'paydays': paydays,
        'monthly_expenses': monthly_expenses,
    }
    
    return render(request, 'home.html', context)

@login_required
def payday(request):
    today_date = timezone.now().date().strftime('%Y-%m-%d')
    # Check if is first payday ever, if it is, prompt start date field
    try:
        last_two_paydays = Payday.objects.all().order_by('-payday_date')[:2]
            
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
            last_two_paydays = Payday.objects.all().order_by('-payday_date')[:2]
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
    categories = Category.objects.all()
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
    if request.method == 'POST':
        amount = request.POST.get('amount')
        monthly_expense_id = request.POST.get('monthly_expense_id')
        #category_id = request.POST.get('category', None)
        note = request.POST.get('note', '')  # Default to an empty string if no note is provided
        monthly_expenses = MonthlyExpenses.objects.get(id=monthly_expense_id)

        try:
            #category = Category.objects.get(id=category_id)
            transaction = Transaction.objects.create(
                user=request.user,
                monthly_expenses=monthly_expenses,
                amount=amount,
                #category=category,
                note=note
            )

            # Return success response with the new transaction data
            return JsonResponse({
                'success': True,
                #'category_name': category.name,
                'amount': amount
            })

        except Category.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Category not found'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def paydays(request):
    paydays = Payday.objects.all()
    if request.method == 'POST':
        # The Delete button is pressed
        payday_id = request.POST.get('payday_id')
        payday_object = Payday.objects.get(id=payday_id)    
        payday_object.delete()

    context = {
        'paydays': paydays
    }

    return render(request, 'paydays.html', context)

@login_required
def monthly_expenses(request, payday_id):
    payday_object = Payday.objects.get(id=payday_id)
    monthly_expenses = MonthlyExpenses.objects.get(payday=payday_object)
    transactions = Transaction.objects.filter(monthly_expenses=monthly_expenses)
    context = {
        'transactions' : transactions
    }

    return render(request, 'monthly_expenses.html', context)