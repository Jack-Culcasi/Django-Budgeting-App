"""
URL configuration for budgeting_app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from home import views  

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('settings/', views.settings, name='settings'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', views.signup, name='signup'),
    path('', views.home, name='home'),
    path('guide/', views.guide, name='guide'),
    path('home/', views.home, name='home'),
    path('payday/', views.payday, name='payday'),
    path('statistics/', views.statistics, name='statistics'),
    path('expenses/<int:payday_id>/<int:monthly_expense_id>/', views.expenses, name='expenses'),
    path('add_transaction/', views.add_transaction, name='add_transaction'),
    path('paydays/', views.paydays, name='paydays'),
    path('amend_payday/<int:payday_id>/', views.amend_payday, name='amend_payday'),
    path('monthly_expenses/<int:payday_id>/', views.monthly_expenses, name='monthly_expenses'),
    path('categories/', views.categories, name='categories'),
    path('delete_transaction/', views.delete_transaction, name='delete_transaction'),
    path('delete_payday/', views.delete_payday, name='delete_payday'),
    path('payday_fixed_costs/<int:payday_id>/<int:monthly_expense_id>/', views.payday_fixed_costs, name='payday_fixed_costs'),
    path('payday_investments/<int:payday_id>/<int:monthly_expense_id>/', views.payday_investments, name='payday_investments'),
    path('payday_pension/<int:payday_id>/<int:monthly_expense_id>/', views.payday_pension, name='payday_pension'),
    path('payday_savings/<int:payday_id>/<int:monthly_expense_id>/', views.payday_savings, name='payday_savings'),
    path('fixed_costs/', views.fixed_costs, name='fixed_costs'),
    path('deductions/<int:payday_id>/<int:monthly_expense_id>/', views.deductions, name='deductions'),
    path('banks/', views.banks, name='banks'),
    path('brokers/', views.brokers, name='brokers'),
    path('investments/', views.investments, name='investments'),
    path('pensions/', views.pensions, name='pensions'),
    path('category/<str:category_name>/', views.category, name='category'),
    path('fixed_cost/<str:fixed_cost_name>/', views.fixed_cost, name='fixed_cost'),
    path('transactions/<int:payday_id>/<int:monthly_expense_id>/', views.transactions, name='transactions'),
    path('add_note/', views.add_note, name='add_note')
]
