import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from .models import Sale, SaleItem
from .forms import SaleMetaForm
from inventory.models import Product, StockMovement
from accounts.decorators import login_required_custom, admin_required
from accounts.middleware import log_action
from accounts.models import AuditLog


@login_required_custom
def pos(request):
    """Main POS / new sale screen."""
    customers = __import__('customers.models', fromlist=['Customer']).Customer.objects.all()
    return render(request, 'sales/pos.html', {'customers': customers})


@login_required_custom
@require_POST
def process_sale(request):
    try:
        data       = json.loads(request.body)
        items_data = data.get('items', [])
        if not items_data:
            return JsonResponse({'ok': False, 'error': 'Cart is empty'}, status=400)

        sale_type    = data.get('sale_type', 'retail')
        payment_mode = data.get('payment_mode', 'cash')
        customer_id  = data.get('customer_id') or None
        discount     = Decimal(str(data.get('discount', '0')))
        notes        = data.get('notes', '')

        sale = Sale.objects.create(
            served_by=request.user,
            sale_type=sale_type,
            payment_mode=payment_mode,
            customer_id=customer_id,
            discount=discount,
            notes=notes,
            total_amount=0,
        )

        total = Decimal('0')
        for item in items_data:
            product = get_object_or_404(Product, pk=item['product_id'])
            qty     = int(item['quantity'])
            price   = Decimal(str(item['unit_price']))
            if product.stock_qty < qty:
                sale.delete()
                return JsonResponse({'ok': False, 'error': f'Insufficient stock for {product.name}'}, status=400)

            before = product.stock_qty
            product.stock_qty -= qty
            product.save()

            SaleItem.objects.create(
                sale=sale, product=product,
                product_name=product.name,
                quantity=qty, unit_price=price,
                subtotal=price * qty,
            )
            StockMovement.objects.create(
                product=product, user=request.user,
                movement_type=StockMovement.TYPE_SALE,
                quantity=qty, qty_before=before, qty_after=product.stock_qty,
                reference_id=sale.pk,
            )
            total += price * qty

        sale.total_amount = total
        sale.save()

        log_action(request.user, AuditLog.ACTION_SALE, 'Sale', sale.pk,
                   f'Sale #{sale.receipt_number()} — KSh {sale.net_total()}', request)

        return JsonResponse({'ok': True, 'sale_id': sale.pk, 'receipt': sale.receipt_number()})

    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@login_required_custom
def sale_receipt(request, pk):
    sale  = get_object_or_404(Sale, pk=pk)
    items = sale.items.all()
    return render(request, 'sales/receipt.html', {'sale': sale, 'items': items})


@login_required_custom
def sale_list(request):
    sales = Sale.objects.select_related('customer', 'served_by').all()
    if not request.user.is_admin():
        sales = sales.filter(served_by=request.user)
    return render(request, 'sales/sale_list.html', {'sales': sales[:100]})


@login_required_custom
def sale_detail(request, pk):
    sale  = get_object_or_404(Sale, pk=pk)
    items = sale.items.select_related('product').all()
    return render(request, 'sales/sale_detail.html', {'sale': sale, 'items': items})



@login_required_custom
def product_search(request):
    from inventory.models import Product
    from django.db.models import Q
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse([], safe=False)
    products = Product.objects.filter(
        Q(name__icontains=q) | Q(sku__icontains=q) | Q(barcode__icontains=q),
        is_active=True
    )[:20]
    data = [{
        'id': p.pk, 'name': p.name,
        'retail_price': str(p.retail_price),
        'wholesale_price': str(p.wholesale_price),
        'stock_qty': p.stock_qty, 'sku': p.sku,
    } for p in products]
    return JsonResponse(data, safe=False)
