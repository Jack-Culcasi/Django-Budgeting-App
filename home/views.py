from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime
from .models import NetWorth, Payday

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
        payday_date = timezone.make_aware(datetime.strptime(payday_date, '%Y-%m-%d'))        
        # Create the Payday object
        payday = Payday.objects.create(
            user=request.user,
            payday_date=payday_date,
            amount=amount
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

    context = {
        'payday': payday,
    }
    return render(request, 'expenses.html', context)