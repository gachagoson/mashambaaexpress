from django import forms
from .models import Sale


class SaleMetaForm(forms.ModelForm):
    class Meta:
        model  = Sale
        fields = ['customer', 'sale_type', 'payment_mode', 'discount', 'notes']
        widgets = {'notes': forms.Textarea(attrs={'rows': 2})}
