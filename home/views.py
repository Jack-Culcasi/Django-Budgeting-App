from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import NetWorth

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
    context = {}
    return render(request, 'payday.html', context)