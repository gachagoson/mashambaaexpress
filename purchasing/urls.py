from django.urls import path
from . import views

app_name = 'purchasing'

urlpatterns = [
    path('suppliers/',             views.supplier_list,   name='supplier_list'),
    path('suppliers/add/',         views.supplier_create, name='supplier_create'),
    path('orders/',                views.po_list,         name='po_list'),
    path('orders/new/',            views.po_create,       name='po_create'),
    path('orders/<int:pk>/',       views.po_detail,       name='po_detail'),
    path('orders/<int:pk>/receive/', views.po_receive,    name='po_receive'),
]
