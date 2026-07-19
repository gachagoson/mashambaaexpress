from django.db import models
from django.conf import settings


class Supplier(models.Model):
    name       = models.CharField(max_length=150)
    phone      = models.CharField(max_length=20, blank=True)
    email      = models.EmailField(blank=True)
    location   = models.CharField(max_length=150, blank=True)
    notes      = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class PurchaseOrder(models.Model):
    STATUS_PENDING   = 'pending'
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES   = [
        (STATUS_PENDING,   'Pending'),
        (STATUS_DELIVERED, 'Delivered'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    supplier    = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, related_name='orders')
    created_by  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    status      = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    total_cost  = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes       = models.TextField(blank=True)
    ordered_at  = models.DateTimeField(auto_now_add=True)
    delivered_at= models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-ordered_at']

    def __str__(self):
        return f"PO #{self.pk} — {self.supplier} — {self.status}"

    def order_number(self):
        return f'PO-{self.pk:04d}'


class PurchaseItem(models.Model):
    order     = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product   = models.ForeignKey('inventory.Product', on_delete=models.SET_NULL, null=True)
    quantity  = models.PositiveIntegerField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal  = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        self.subtotal = self.unit_cost * self.quantity
        super().save(*args, **kwargs)
