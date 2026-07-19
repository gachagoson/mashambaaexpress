from django.contrib import admin
from .models import Expense


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['date', 'description', 'category', 'amount', 'recorded_by']
    list_filter  = ['category', 'date']
