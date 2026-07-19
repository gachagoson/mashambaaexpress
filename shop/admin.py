from django.contrib import admin
from .models import ShopCustomer, ShopOrder, ShopOrderItem, MpesaTransaction


@admin.register(ShopCustomer)
class ShopCustomerAdmin(admin.ModelAdmin):
    list_display  = ['full_name', 'email', 'phone', 'location', 'is_active', 'created_at']
    search_fields = ['full_name', 'email', 'phone']
    list_filter   = ['is_active']


class ShopOrderItemInline(admin.TabularInline):
    model   = ShopOrderItem
    extra   = 0
    readonly_fields = ['subtotal']


class MpesaInline(admin.TabularInline):
    model   = MpesaTransaction
    extra   = 0
    readonly_fields = ['checkout_request_id', 'mpesa_receipt', 'status', 'amount', 'created_at']


@admin.register(ShopOrder)
class ShopOrderAdmin(admin.ModelAdmin):
    list_display   = ['order_number', 'customer', 'status', 'payment_status', 'total_amount', 'created_at']
    list_filter    = ['status', 'payment_status']
    inlines        = [ShopOrderItemInline, MpesaInline]
    readonly_fields= ['order_number', 'created_at', 'updated_at', 'confirmed_at']
    search_fields  = ['order_number', 'customer__full_name', 'customer__email']
