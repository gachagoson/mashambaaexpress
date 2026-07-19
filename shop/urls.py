from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    # Storefront
    path('',                                views.shop_home,          name='home'),
    path('product/<int:pk>/',               views.product_detail,     name='product_detail'),
    # Auth
    path('register/',                       views.shop_register,      name='register'),
    path('login/',                          views.shop_login,         name='login'),
    path('logout/',                         views.shop_logout,        name='logout'),
    # Cart
    path('cart/',                           views.cart_view,          name='cart'),
    path('cart/add/<int:pk>/',              views.cart_add,           name='cart_add'),
    path('cart/update/<int:pk>/',           views.cart_update,        name='cart_update'),
    path('cart/remove/<int:pk>/',           views.cart_remove,        name='cart_remove'),
    # Checkout & payment
    path('checkout/',                       views.checkout,           name='checkout'),
    path('order/<str:order_number>/pending/', views.order_pending,   name='order_pending'),
    path('order/<str:order_number>/status/', views.payment_status,   name='payment_status'),
    path('order/<str:order_number>/retry/', views.retry_payment,     name='retry_payment'),
    path('mpesa/callback/',                 views.mpesa_callback,     name='mpesa_callback'),
    # Customer account
    path('my-orders/',                      views.my_orders,          name='my_orders'),
    path('my-orders/<str:order_number>/',   views.order_detail,       name='order_detail'),
    # Admin order management
    path('admin/orders/',                   views.admin_orders,       name='admin_orders'),
    path('admin/orders/<str:order_number>/',views.admin_order_detail, name='admin_order_detail'),
    path('admin/orders/<str:order_number>/action/', views.admin_order_action, name='admin_order_action'),
]
