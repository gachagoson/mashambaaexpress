from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Count, F
from django.db.models.functions import TruncDay, TruncMonth
from django.utils import timezone
from datetime import timedelta, date
import json
from .models import Expense
from .forms import ExpenseForm
from sales.models import Sale, SaleItem
from inventory.models import Product
from accounts.decorators import admin_required


@admin_required
def dashboard(request):
    today    = timezone.localdate()
    week_ago = today - timedelta(days=6)

    today_sales   = Sale.objects.filter(created_at__date=today)
    today_revenue = today_sales.aggregate(t=Sum('total_amount'))['t'] or 0
    today_count   = today_sales.count()

    week_sales = Sale.objects.filter(created_at__date__gte=week_ago)
    week_revenue = week_sales.aggregate(t=Sum('total_amount'))['t'] or 0

    low_stock = Product.objects.filter(is_active=True).extra(
        where=['stock_qty <= low_stock_alert']
    )[:8]

    # Daily revenue for chart (last 7 days)
    daily = (Sale.objects
             .filter(created_at__date__gte=week_ago)
             .annotate(day=TruncDay('created_at'))
             .values('day')
             .annotate(revenue=Sum('total_amount'))
             .order_by('day'))

    chart_labels  = [(today - timedelta(days=i)).strftime('%d %b') for i in range(6, -1, -1)]
    daily_map     = {d['day'].date(): float(d['revenue'] or 0) for d in daily}
    chart_data    = [daily_map.get(today - timedelta(days=i), 0) for i in range(6, -1, -1)]

    stock_value = sum((p.stock_value() for p in Product.objects.filter(is_active=True)), 0)

    return render(request, 'reports/dashboard.html', {
        'today_revenue': today_revenue,
        'today_count'  : today_count,
        'week_revenue' : week_revenue,
        'low_stock'    : low_stock,
        'chart_labels' : json.dumps(chart_labels),
        'chart_data'   : json.dumps(chart_data),
        'stock_value'  : stock_value,
    })


@admin_required
def sales_report(request):
    date_from = request.GET.get('from', (date.today() - timedelta(days=29)).isoformat())
    date_to   = request.GET.get('to', date.today().isoformat())
    sales     = Sale.objects.filter(created_at__date__gte=date_from, created_at__date__lte=date_to)
    total     = sales.aggregate(t=Sum('total_amount'))['t'] or 0
    by_type   = sales.values('sale_type').annotate(total=Sum('total_amount'), count=Count('id'))
    by_payment= sales.values('payment_mode').annotate(total=Sum('total_amount'))
    return render(request, 'reports/sales_report.html', {
        'sales': sales.order_by('-created_at')[:200],
        'total': total,
        'by_type': by_type,
        'by_payment': by_payment,
        'date_from': date_from,
        'date_to': date_to,
    })


@admin_required
def stock_report(request):
    products = Product.objects.select_related('category').filter(is_active=True).order_by('name')
    total_value = sum(p.stock_value() for p in products)
    return render(request, 'reports/stock_report.html', {
        'products': products, 'total_value': total_value
    })


@admin_required
def expense_list(request):
    expenses = Expense.objects.select_related('recorded_by').all()
    total    = expenses.aggregate(t=Sum('amount'))['t'] or 0
    return render(request, 'reports/expense_list.html', {'expenses': expenses, 'total': total})


@admin_required
def expense_create(request):
    form = ExpenseForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        expense = form.save(commit=False)
        expense.recorded_by = request.user
        expense.save()
        messages.success(request, 'Expense recorded.')
        return redirect('reports:expense_list')
    return render(request, 'reports/expense_form.html', {'form': form})
