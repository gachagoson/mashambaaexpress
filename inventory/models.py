from django.db import models
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name="products"
    )

    # CORE IDENTITY
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True, blank=True)

    # 🔥 ADD THIS (YOU WERE RIGHT)
    barcode = models.CharField(max_length=100, unique=True, null=True, blank=True)

    description = models.TextField(blank=True)

    # PRICING SYSTEM
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    retail_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    wholesale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    old_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    # STOCK SYSTEM
    stock_qty = models.IntegerField(default=0)
    low_stock_alert = models.IntegerField(default=5)

    # IMAGES
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    image_hover = models.ImageField(upload_to="products/", blank=True, null=True)

    # OLD STORE FLAGS (for frontend compatibility)
    rating = models.FloatField(default=0.0)

    is_new = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    is_best_seller = models.BooleanField(default=False)
    is_top_rated = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_deal_of_day = models.BooleanField(default=False)

    # SYSTEM FLAGS
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.sku:
            import uuid

            self.sku = "GB-" + uuid.uuid4().hex[:8].upper()

        super().save(*args, **kwargs)


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="gallery"
    )
    image = models.ImageField(upload_to="products/gallery/")


class StockMovement(models.Model):
    TYPE_SALE = "sale"
    TYPE_PURCHASE = "purchase"
    TYPE_ADJUST_IN = "adjust_in"
    TYPE_ADJUST_OUT = "adjust_out"
    TYPE_RETURN = "return"

    TYPE_CHOICES = [
        (TYPE_SALE, "Sale"),
        (TYPE_PURCHASE, "Purchase / restock"),
        (TYPE_ADJUST_IN, "Manual add"),
        (TYPE_ADJUST_OUT, "Manual remove"),
        (TYPE_RETURN, "Customer return"),
    ]

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="movements"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    movement_type = models.CharField(max_length=15, choices=TYPE_CHOICES)
    quantity = models.IntegerField()
    qty_before = models.IntegerField()
    qty_after = models.IntegerField()
    reason = models.CharField(max_length=255, blank=True)
    reference_id = models.PositiveIntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.product} | {self.movement_type} | {self.quantity:+d}"
