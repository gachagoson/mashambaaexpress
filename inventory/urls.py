from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('',                            views.product_list,      name='product_list'),
    path('products/add/',               views.product_create,    name='product_create'),
    path('products/<int:pk>/',          views.product_detail,    name='product_detail'),
    path('products/<int:pk>/edit/',     views.product_edit,      name='product_edit'),
    path('products/<int:pk>/adjust/',   views.stock_adjust,      name='stock_adjust'),
    path('barcode/lookup/',             views.barcode_lookup,    name='barcode_lookup'),
    path('barcode/stock-in/',           views.barcode_stock_in,  name='barcode_stock_in'),
    path('categories/',                 views.category_list,     name='category_list'),
    path('categories/add/',             views.category_create,   name='category_create'),
]
