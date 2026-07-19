from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Customer
from .forms import CustomerForm
from accounts.decorators import login_required_custom


@login_required_custom
def customer_list(request):
    customers = Customer.objects.all()
    q = request.GET.get('q', '')
    if q:
        customers = customers.filter(name__icontains=q)
    return render(request, 'customers/customer_list.html', {'customers': customers, 'q': q})


@login_required_custom
def customer_create(request):
    form = CustomerForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        customer = form.save()
        messages.success(request, f'Customer {customer.name} added.')
        next_url = request.GET.get('next', 'customers:customer_list')
        return redirect(next_url)
    return render(request, 'customers/customer_form.html', {'form': form})


@login_required_custom
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    sales    = customer.sales.select_related('served_by').order_by('-created_at')[:20]
    return render(request, 'customers/customer_detail.html', {'customer': customer, 'sales': sales})
