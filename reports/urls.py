from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('',               views.dashboard,      name='dashboard'),
    path('sales/',         views.sales_report,   name='sales_report'),
    path('stock/',         views.stock_report,   name='stock_report'),
    path('expenses/',      views.expense_list,   name='expense_list'),
    path('expenses/add/',  views.expense_create, name='expense_create'),
]
