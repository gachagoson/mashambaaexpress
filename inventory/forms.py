from django import forms
from .models import Product, Category, StockMovement


class ProductForm(forms.ModelForm):
    class Meta:
        model  = Product
        fields = ['name', 'category', 'sku', 'barcode', 'description',
                  'cost_price', 'retail_price', 'wholesale_price',
                  'stock_qty', 'low_stock_alert', 'image', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'barcode': forms.TextInput(attrs={'id': 'barcode-input', 'placeholder': 'Scan or type barcode'}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model  = Category
        fields = ['name', 'description']


class StockAdjustForm(forms.Form):
    ADJUST_IN  = 'adjust_in'
    ADJUST_OUT = 'adjust_out'
    TYPE_CHOICES = [(ADJUST_IN, 'Add stock'), (ADJUST_OUT, 'Remove stock')]

    adjustment_type = forms.ChoiceField(choices=TYPE_CHOICES, widget=forms.RadioSelect)
    quantity        = forms.IntegerField(min_value=1)
    reason          = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'placeholder': 'Reason (optional)'}))


class BarcodeStockInForm(forms.Form):
    barcode  = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Scan barcode...', 'autofocus': True}))
    quantity = forms.IntegerField(min_value=1, initial=1)
