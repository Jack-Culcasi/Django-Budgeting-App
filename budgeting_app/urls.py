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
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', auth_views.LoginView.as_view(template_name='signup.html'), name='signup'),
    path('', views.home, name='home'),
    path('home/', views.home, name='home'),
    path('payday/', views.payday, name='payday'),
    path('expenses/<int:payday_id>/<int:monthly_expense_id>/', views.expenses, name='expenses'),
    path('add_transaction/', views.add_transaction, name='add_transaction'),
    path('paydays/', views.paydays, name='paydays'),
    path('monthly_expenses/<int:payday_id>/', views.monthly_expenses, name='monthly_expenses'),
    path('categories/', views.categories, name='categories'),
    path('delete_transaction/', views.delete_transaction, name='delete_transaction'),
    path('delete_payday/', views.delete_payday, name='delete_payday'),
    path('payday_fixed_costs/<int:payday_id>/<int:monthly_expense_id>/', views.payday_fixed_costs, name='payday_fixed_costs'),
    path('fixed_costs/', views.fixed_costs, name='fixed_costs'),
    path('deductions/<int:payday_id>/<int:monthly_expense_id>/', views.deductions, name='deductions'),
    path('first_time_user/', views.first_time_user, name='first_time_user'),

]
