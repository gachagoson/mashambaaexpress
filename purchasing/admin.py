from django.contrib import admin
from .models import Supplier, PurchaseOrder, PurchaseItem


class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 0


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display  = ['name', 'phone', 'location']
    search_fields = ['name']


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'supplier', 'status', 'total_cost', 'ordered_at']
    list_filter  = ['status']
    inlines      = [PurchaseItemInline]
