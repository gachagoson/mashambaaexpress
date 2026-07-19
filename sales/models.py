from django.db import models
from django.conf import settings


class Sale(models.Model):
    TYPE_RETAIL    = 'retail'
    TYPE_WHOLESALE = 'wholesale'
    TYPE_CHOICES   = [(TYPE_RETAIL, 'Retail'), (TYPE_WHOLESALE, 'Wholesale')]

    PAY_CASH   = 'cash'
    PAY_MPESA  = 'mpesa'
    PAY_BANK   = 'bank'
    PAY_CHOICES = [
        (PAY_CASH,  'Cash'),
        (PAY_MPESA, 'M-Pesa'),
        (PAY_BANK,  'Bank transfer'),
    ]

    customer      = models.ForeignKey('customers.Customer', on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    served_by     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='sales')
    sale_type     = models.CharField(max_length=10, choices=TYPE_CHOICES, default=TYPE_RETAIL)
    payment_mode  = models.CharField(max_length=10, choices=PAY_CHOICES, default=PAY_CASH)
    total_amount  = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount      = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes         = models.TextField(blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Sale #{self.pk} — {self.created_at:%Y-%m-%d} — KSh {self.total_amount}"

    def net_total(self):
        return self.total_amount - self.discount

    def receipt_number(self):
        return f'GB-{self.pk:05d}'


class SaleItem(models.Model):
    sale        = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product     = models.ForeignKey('inventory.Product', on_delete=models.SET_NULL, null=True)
    product_name= models.CharField(max_length=200)
    quantity    = models.PositiveIntegerField()
    unit_price  = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal    = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product_name} x {self.quantity} @ {self.unit_price}"
