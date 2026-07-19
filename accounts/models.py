from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_ADMIN = 'admin'
    ROLE_WORKER = 'worker'
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_WORKER, 'Worker'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_WORKER)
    phone = models.CharField(max_length=20, blank=True)

    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"


class AuditLog(models.Model):
    ACTION_CREATE = 'create'
    ACTION_UPDATE = 'update'
    ACTION_DELETE = 'delete'
    ACTION_LOGIN  = 'login'
    ACTION_LOGOUT = 'logout'
    ACTION_SALE   = 'sale'
    ACTION_STOCK  = 'stock'

    ACTION_CHOICES = [
        (ACTION_CREATE, 'Created'),
        (ACTION_UPDATE, 'Updated'),
        (ACTION_DELETE, 'Deleted'),
        (ACTION_LOGIN,  'Logged in'),
        (ACTION_LOGOUT, 'Logged out'),
        (ACTION_SALE,   'Sale processed'),
        (ACTION_STOCK,  'Stock adjusted'),
    ]

    user       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action     = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50, blank=True)
    object_id  = models.PositiveIntegerField(null=True, blank=True)
    detail     = models.TextField(blank=True)
    timestamp  = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} — {self.action} at {self.timestamp:%Y-%m-%d %H:%M}"
