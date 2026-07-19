from django.contrib.auth.backends import ModelBackend
from .models import ShopCustomer


class ShopCustomerBackend(ModelBackend):
    """Auth backend for ShopCustomer (separate from staff User model)."""

    def authenticate(self, request, email=None, password=None, **kwargs):
        try:
            user = ShopCustomer.objects.get(email=email)
            if user.check_password(password) and user.is_active:
                return user
        except ShopCustomer.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return ShopCustomer.objects.get(pk=user_id)
        except ShopCustomer.DoesNotExist:
            return None
