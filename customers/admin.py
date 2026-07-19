from django.contrib import admin
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display  = ['name', 'customer_type', 'phone', 'location', 'created_at']
    list_filter   = ['customer_type']
    search_fields = ['name', 'phone']
