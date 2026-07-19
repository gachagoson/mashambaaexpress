from functools import wraps
from django.shortcuts import redirect


def shop_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('shop_customer_id'):
            return redirect('shop:login')
        return view_func(request, *args, **kwargs)
    return wrapper
