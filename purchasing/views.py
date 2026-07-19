from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import Supplier, PurchaseOrder, PurchaseItem
from .forms import SupplierForm, PurchaseOrderForm, PurchaseItemFormSet
from inventory.models import StockMovement
from accounts.decorators import admin_required
from accounts.middleware import log_action
from accounts.models import AuditLog


@admin_required
def supplier_list(request):
    suppliers = Supplier.objects.all()
    return render(request, 'purchasing/supplier_list.html', {'suppliers': suppliers})


@admin_required
def supplier_create(request):
    form = SupplierForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Supplier added.')
        return redirect('purchasing:supplier_list')
    return render(request, 'purchasing/supplier_form.html', {'form': form})


@admin_required
def po_list(request):
    orders = PurchaseOrder.objects.select_related('supplier', 'created_by').all()
    return render(request, 'purchasing/po_list.html', {'orders': orders})


@admin_required
def po_create(request):
    form    = PurchaseOrderForm(request.POST or None)
    formset = PurchaseItemFormSet(request.POST or None)
    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        order = form.save(commit=False)
        order.created_by = request.user
        order.save()
        items = formset.save(commit=False)
        total = 0
        for item in items:
            item.order = order
            item.save()
            total += item.subtotal
        order.total_cost = total
        order.save()
        log_action(request.user, AuditLog.ACTION_CREATE, 'PurchaseOrder', order.pk, f'Created {order.order_number()}', request)
        messages.success(request, f'Purchase order {order.order_number()} created.')
        return redirect('purchasing:po_detail', pk=order.pk)
    return render(request, 'purchasing/po_form.html', {'form': form, 'formset': formset, 'title': 'New purchase order'})


@admin_required
def po_detail(request, pk):
    order = get_object_or_404(PurchaseOrder, pk=pk)
    items = order.items.select_related('product').all()
    return render(request, 'purchasing/po_detail.html', {'order': order, 'items': items})


@admin_required
def po_receive(request, pk):
    order = get_object_or_404(PurchaseOrder, pk=pk, status=PurchaseOrder.STATUS_PENDING)
    if request.method == 'POST':
        for item in order.items.select_related('product').all():
            if item.product:
                before = item.product.stock_qty
                item.product.stock_qty += item.quantity
                item.product.save()
                StockMovement.objects.create(
                    product=item.product, user=request.user,
                    movement_type=StockMovement.TYPE_PURCHASE,
                    quantity=item.quantity, qty_before=before,
                    qty_after=item.product.stock_qty,
                    reference_id=order.pk,
                )
        order.status       = PurchaseOrder.STATUS_DELIVERED
        order.delivered_at = timezone.now()
        order.save()
        log_action(request.user, AuditLog.ACTION_STOCK, 'PurchaseOrder', order.pk,
                   f'Received stock for {order.order_number()}', request)
        messages.success(request, f'Stock received for {order.order_number()}.')
        return redirect('purchasing:po_detail', pk=pk)
    return render(request, 'purchasing/po_receive_confirm.html', {'order': order})
