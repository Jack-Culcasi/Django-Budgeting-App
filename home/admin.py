from django.contrib import admin
from .models import Payday, MonthlyExpenses, Broker, Bank, Pension, NetWorth

@admin.register(Payday)
class PaydayAdmin(admin.ModelAdmin):
    list_display = ('user', 'payday_date', 'amount', 'note')
    search_fields = ('user__username', 'payday_date')
    list_filter = ('payday_date',)

@admin.register(MonthlyExpenses)
class MonthlyExpensesAdmin(admin.ModelAdmin):
    list_display = ('payday', 'start_date', 'end_date', 'amount', 'utilities', 'groceries', 'misc')
    search_fields = ('payday__user__username', 'start_date', 'end_date')
    list_filter = ('start_date', 'end_date')

@admin.register(Broker)
class BrokerAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'amount', 'latest_update', 'note')
    search_fields = ('user__username', 'name')
    list_filter = ('latest_update',)

@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'amount', 'latest_update', 'note')
    search_fields = ('user__username', 'name')
    list_filter = ('latest_update',)

@admin.register(Pension)
class PensionAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'amount', 'latest_update', 'note')
    search_fields = ('user__username', 'name')
    list_filter = ('latest_update',)

@admin.register(NetWorth)
class NetWorthAdmin(admin.ModelAdmin):
    list_display = ('user', 'payday', 'date', 'total_savings', 'total_investments', 'total_pension', 'net_worth', 'note')
    search_fields = ('user__username', 'date')
    list_filter = ('date',)
