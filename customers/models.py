from django.db import models


class Customer(models.Model):
    TYPE_RETAIL     = 'retail'
    TYPE_WHOLESALE  = 'wholesale'
    TYPE_CHOICES    = [(TYPE_RETAIL, 'Retail'), (TYPE_WHOLESALE, 'Wholesaler')]

    name       = models.CharField(max_length=150)
    phone      = models.CharField(max_length=20, blank=True)
    email      = models.EmailField(blank=True)
    location   = models.CharField(max_length=150, blank=True)
    customer_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=TYPE_RETAIL)
    notes      = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_customer_type_display()})"
