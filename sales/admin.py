from django.contrib import admin
from .models import Sale, SaleItem


class SaleItemInline(admin.TabularInline):
    model  = SaleItem
    extra  = 0
    readonly_fields = ['subtotal']


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display  = ['receipt_number', 'created_at', 'customer', 'sale_type', 'payment_mode', 'total_amount', 'served_by']
    list_filter   = ['sale_type', 'payment_mode', 'created_at']
    inlines       = [SaleItemInline]
    readonly_fields = ['created_at', 'total_amount']
