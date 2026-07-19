from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect


def root_redirect(request):
    if request.user.is_authenticated:
        if request.user.is_admin():
            return redirect('reports:dashboard')
        return redirect('sales:pos')
    return redirect('accounts:login')


urlpatterns = [
    path('',           root_redirect,            name='dashboard'),
    path('admin/',     admin.site.urls),
    path('accounts/',  include('accounts.urls')),
    path('inventory/', include('inventory.urls')),
    path('sales/',     include('sales.urls')),
    path('purchasing/',include('purchasing.urls')),
    path('customers/', include('customers.urls')),
    path('reports/',   include('reports.urls')),
    path('shop/',      include('shop.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
