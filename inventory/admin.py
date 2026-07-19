from django.contrib import admin
from .models import Category, Product, StockMovement


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ['name', 'description']
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display  = ['name', 'sku', 'category', 'retail_price', 'stock_qty', 'is_active']
    list_filter   = ['category', 'is_active']
    search_fields = ['name', 'sku', 'barcode']


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display  = ['timestamp', 'product', 'movement_type', 'quantity', 'qty_before', 'qty_after', 'user']
    list_filter   = ['movement_type']
    readonly_fields = ['timestamp']
