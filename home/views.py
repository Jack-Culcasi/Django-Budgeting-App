from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from datetime import datetime
from .models import NetWorth, Payday, Category, Transaction

@login_required
def home(request):    
    if NetWorth.objects.filter(user=request.user).exists():
        net_worth = NetWorth.objects.filter(user=request.user).latest('date')
    else:
        net_worth = 0  # Handle the case when no record exists
    
    # Prepare the context for template
    context = {
        'net_worth': net_worth
    }
    
    return render(request, 'home.html', context)

@login_required
def payday(request):

    if request.method == 'POST':
        # Get the form data
        amount = request.POST.get('amount')
        payday_date = request.POST.get('date')
        note = request.POST.get('note', None)
        payday_date = timezone.make_aware(datetime.strptime(payday_date, '%Y-%m-%d'))        
        # Create the Payday object
        payday = Payday.objects.create(
            user=request.user,
            payday_date=payday_date,
            amount=amount,
            note=note
        )
        return redirect('expenses', payday_id=payday.id)

    today_date = timezone.now().date().strftime('%Y-%m-%d')  # Get the current date

    context = {
        'today_date': today_date
    }

    return render(request, 'payday.html', context)

@login_required
def expenses(request, payday_id=None):
    # Redirect to payday if accessed directly without a payday_id
    if payday_id is None:
        return redirect('payday')

    try:
        payday = Payday.objects.get(id=payday_id, user=request.user)
    except Payday.DoesNotExist:
        return redirect('payday')
    
    categories = Category.objects.all()
    transactions = Transaction.objects.filter(user=request.user)

    context = {
        'payday': payday,
        'categories': categories,
        'transactions': transactions,
    }
    return render(request, 'expenses.html', context)

@login_required
def add_transaction(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')
        #category_id = request.POST.get('category', None)
        note = request.POST.get('note', '')  # Default to an empty string if no note is provided

        try:
            #category = Category.objects.get(id=category_id)
            transaction = Transaction.objects.create(
                user=request.user,
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
    return render(request, 'paydays.html')