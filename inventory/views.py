from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import Product, Category, StockMovement
from .forms import ProductForm, CategoryForm, StockAdjustForm, BarcodeStockInForm
from accounts.decorators import admin_required, login_required_custom
from accounts.middleware import log_action
from accounts.models import AuditLog


@login_required_custom
def product_list(request):
    q        = request.GET.get('q', '')
    category = request.GET.get('category', '')
    stock    = request.GET.get('stock', '')
    products = Product.objects.select_related('category').filter(is_active=True)
    if q:
        products = products.filter(Q(name__icontains=q) | Q(sku__icontains=q) | Q(barcode__icontains=q))
    if category:
        products = products.filter(category_id=category)
    if stock == 'low':
        products = [p for p in products if p.is_low_stock()]
    elif stock == 'out':
        products = [p for p in products if p.is_out_of_stock()]
    categories = Category.objects.all()
    return render(request, 'inventory/product_list.html', {
        'products': products, 'categories': categories,
        'q': q, 'selected_category': category, 'stock_filter': stock
    })


@login_required_custom
def product_detail(request, pk):
    product   = get_object_or_404(Product, pk=pk)
    movements = product.movements.select_related('user').all()[:20]
    return render(request, 'inventory/product_detail.html', {'product': product, 'movements': movements})


@admin_required
def product_create(request):
    form = ProductForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        product = form.save()
        log_action(request.user, AuditLog.ACTION_CREATE, 'Product', product.pk, f'Created {product.name}', request)
        messages.success(request, f'Product "{product.name}" added.')
        return redirect('inventory:product_list')
    return render(request, 'inventory/product_form.html', {'form': form, 'title': 'Add product'})


@admin_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form    = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == 'POST' and form.is_valid():
        form.save()
        log_action(request.user, AuditLog.ACTION_UPDATE, 'Product', product.pk, f'Updated {product.name}', request)
        messages.success(request, 'Product updated.')
        return redirect('inventory:product_detail', pk=pk)
    return render(request, 'inventory/product_form.html', {'form': form, 'title': f'Edit {product.name}', 'product': product})


@admin_required
def stock_adjust(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form    = StockAdjustForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        adj_type = form.cleaned_data['adjustment_type']
        qty      = form.cleaned_data['quantity']
        reason   = form.cleaned_data['reason']
        before   = product.stock_qty
        if adj_type == 'adjust_in':
            product.stock_qty += qty
        else:
            product.stock_qty = max(0, product.stock_qty - qty)
        product.save()
        StockMovement.objects.create(
            product=product, user=request.user, movement_type=adj_type,
            quantity=qty, qty_before=before, qty_after=product.stock_qty, reason=reason
        )
        log_action(request.user, AuditLog.ACTION_STOCK, 'Product', product.pk,
                   f'{adj_type} {qty} units of {product.name}. Reason: {reason}', request)
        messages.success(request, f'Stock updated. New qty: {product.stock_qty}')
        return redirect('inventory:product_detail', pk=pk)
    return render(request, 'inventory/stock_adjust.html', {'form': form, 'product': product})


@login_required_custom
def barcode_lookup(request):
    barcode = request.GET.get('barcode', '').strip()
    mode    = request.GET.get('mode', 'sale')
    if not barcode:
        return JsonResponse({'found': False})
    try:
        product = Product.objects.get(barcode=barcode, is_active=True)
        return JsonResponse({
            'found': True,
            'id': product.pk,
            'name': product.name,
            'retail_price': str(product.retail_price),
            'wholesale_price': str(product.wholesale_price),
            'stock_qty': product.stock_qty,
            'sku': product.sku,
        })
    except Product.DoesNotExist:
        return JsonResponse({'found': False, 'barcode': barcode})


@admin_required
def barcode_stock_in(request):
    form    = BarcodeStockInForm(request.POST or None)
    product = None
    if request.method == 'POST' and form.is_valid():
        barcode = form.cleaned_data['barcode']
        qty     = form.cleaned_data['quantity']
        try:
            product = Product.objects.get(barcode=barcode)
            before  = product.stock_qty
            product.stock_qty += qty
            product.save()
            StockMovement.objects.create(
                product=product, user=request.user, movement_type='purchase',
                quantity=qty, qty_before=before, qty_after=product.stock_qty,
                reason='Barcode stock-in'
            )
            messages.success(request, f'Added {qty} units to "{product.name}". New stock: {product.stock_qty}')
            return redirect('inventory:barcode_stock_in')
        except Product.DoesNotExist:
            messages.warning(request, f'Barcode {barcode} not found. Create the product first.')
            return redirect(f'/inventory/products/add/?barcode={barcode}')
    return render(request, 'inventory/barcode_stock_in.html', {'form': form})


@login_required_custom
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'inventory/category_list.html', {'categories': categories})


@admin_required
def category_create(request):
    form = CategoryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Category added.')
        return redirect('inventory:category_list')
    return render(request, 'inventory/category_form.html', {'form': form, 'title': 'Add category'})
