from django.db import models
from django.conf import settings


class Expense(models.Model):
    CAT_RENT      = 'rent'
    CAT_SALARY    = 'salary'
    CAT_UTILITIES = 'utilities'
    CAT_TRANSPORT = 'transport'
    CAT_SUPPLIES  = 'supplies'
    CAT_OTHER     = 'other'
    CAT_CHOICES   = [
        (CAT_RENT,      'Rent'),
        (CAT_SALARY,    'Salary'),
        (CAT_UTILITIES, 'Utilities'),
        (CAT_TRANSPORT, 'Transport'),
        (CAT_SUPPLIES,  'Supplies'),
        (CAT_OTHER,     'Other'),
    ]

    description  = models.CharField(max_length=255)
    amount       = models.DecimalField(max_digits=10, decimal_places=2)
    category     = models.CharField(max_length=15, choices=CAT_CHOICES, default=CAT_OTHER)
    recorded_by  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    date         = models.DateField()
    notes        = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.description} — KSh {self.amount} ({self.date})"
