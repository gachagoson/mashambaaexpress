from django import forms
from django.forms import inlineformset_factory
from .models import Supplier, PurchaseOrder, PurchaseItem


class SupplierForm(forms.ModelForm):
    class Meta:
        model  = Supplier
        fields = ['name', 'phone', 'email', 'location', 'notes']


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model  = PurchaseOrder
        fields = ['supplier', 'notes']


PurchaseItemFormSet = inlineformset_factory(
    PurchaseOrder, PurchaseItem,
    fields=['product', 'quantity', 'unit_cost'],
    extra=3, can_delete=True,
    widgets={'unit_cost': forms.NumberInput(attrs={'step': '0.01'})}
)
