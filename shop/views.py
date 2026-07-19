import json
import logging
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q

from inventory.models import Product, Category
from .models import ShopCustomer, ShopOrder, ShopOrderItem, MpesaTransaction
from .cart import Cart
from .forms import RegisterForm, LoginForm, CheckoutForm
from .decorators import shop_login_required
from . import mpesa as mpesa_service

logger = logging.getLogger(__name__)

# ─── helpers ────────────────────────────────────────────────
SESSION_CUSTOMER = "shop_customer_id"


def get_shop_customer(request):
    cid = request.session.get(SESSION_CUSTOMER)
    if not cid:
        return None
    try:
        return ShopCustomer.objects.get(pk=cid, is_active=True)
    except ShopCustomer.DoesNotExist:
        return None


# ─── auth ───────────────────────────────────────────────────
def shop_register(request):
    if get_shop_customer(request):
        return redirect("shop:home")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        customer = form.save()
        request.session[SESSION_CUSTOMER] = customer.pk
        messages.success(
            request, f"Welcome, {customer.full_name}! Your account is ready."
        )
        return redirect("shop:home")
    return render(request, "shop/register.html", {"form": form})


def shop_login(request):
    if get_shop_customer(request):
        return redirect("shop:home")
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]
        try:
            customer = ShopCustomer.objects.get(email=email, is_active=True)
            if customer.check_password(password):
                request.session[SESSION_CUSTOMER] = customer.pk
                messages.success(request, f"Welcome back, {customer.full_name}!")
                return redirect(request.GET.get("next", "shop:home"))
        except ShopCustomer.DoesNotExist:
            pass
        form.add_error(None, "Invalid email or password.")
    return render(request, "shop/login.html", {"form": form})


def shop_logout(request):
    request.session.pop(SESSION_CUSTOMER, None)
    return redirect("shop:home")


# ─── storefront ─────────────────────────────────────────────
def shop_home(request):
    q = request.GET.get("q", "")
    category = request.GET.get("cat", "")
    categories = Category.objects.all()
    products = Product.objects.filter(is_active=True).select_related("category")
    if q:
        products = products.filter(Q(name__icontains=q) | Q(description__icontains=q))
    if category:
        products = products.filter(category_id=category)
    featured = products.order_by("-id")[:8]
    return render(
        request,
        "shop/home.html",
        {
            "products": products,
            "featured": featured,
            "categories": categories,
            "q": q,
            "selected_cat": category,
            "customer": get_shop_customer(request),
        },
    )


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    related = Product.objects.filter(category=product.category, is_active=True).exclude(
        pk=pk
    )[:4]
    customer = get_shop_customer(request)
    return render(
        request,
        "shop/product_detail.html",
        {
            "product": product,
            "related": related,
            "customer": customer,
        },
    )


# ─── cart ───────────────────────────────────────────────────
def cart_view(request):
    cart = Cart(request)
    customer = get_shop_customer(request)
    return render(request, "shop/cart.html", {"cart": cart, "customer": customer})


@require_POST
def cart_add(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    cart = Cart(request)
    qty = int(request.POST.get("qty", 1))
    cart.add(product, qty)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "count": len(cart)})
    messages.success(request, f'"{product.name}" added to cart.')
    return redirect("shop:cart")


@require_POST
def cart_update(request, pk):
    cart = Cart(request)
    qty = int(request.POST.get("qty", 1))
    cart.update(pk, qty)
    return redirect("shop:cart")


@require_POST
def cart_remove(request, pk):
    cart = Cart(request)
    cart.remove(pk)
    return redirect("shop:cart")


# ─── checkout ───────────────────────────────────────────────
@shop_login_required
def checkout(request):
    cart = Cart(request)
    customer = get_shop_customer(request)
    if not len(cart):
        messages.warning(request, "Your cart is empty.")
        return redirect("shop:home")

    form = CheckoutForm(
        request.POST or None,
        initial={
            "delivery_phone": customer.phone,
            "delivery_address": customer.location,
        },
    )

    if request.method == "POST" and form.is_valid():
        # Create the order (no stock change yet — admin confirms first)
        order = ShopOrder.objects.create(
            customer=customer,
            delivery_address=form.cleaned_data["delivery_address"],
            delivery_phone=form.cleaned_data["delivery_phone"],
            notes=form.cleaned_data["notes"],
            total_amount=cart.total(),
        )
        for item in cart:
            ShopOrderItem.objects.create(
                order=order,
                product=item["product"],
                product_name=item["name"],
                product_sku=item["product"].sku,
                quantity=item["qty"],
                unit_price=item["price"],
                subtotal=item["subtotal"],
            )

        # Initiate M-Pesa STK push
        phone = mpesa_service.format_phone(form.cleaned_data["delivery_phone"])
        amount = int(cart.total())
        result = mpesa_service.stk_push(phone, amount, order.order_number)

        if result.get("success"):
            MpesaTransaction.objects.create(
                order=order,
                phone=phone,
                amount=amount,
                checkout_request_id=result["checkout_request_id"],
                merchant_request_id=result["merchant_request_id"],
            )
            cart.clear()
            return redirect("shop:order_pending", order_number=order.order_number)
        else:
            # STK failed — still save order, let customer try again
            order.payment_status = ShopOrder.PAY_FAILED
            order.save()
            cart.clear()
            messages.warning(
                request,
                f'Order placed but M-Pesa prompt failed: {result.get("error")}. You can retry payment from My Orders.',
            )
            return redirect("shop:my_orders")

    return render(
        request,
        "shop/checkout.html",
        {
            "form": form,
            "cart": cart,
            "customer": customer,
        },
    )


def order_pending(request, order_number):
    order = get_object_or_404(ShopOrder, order_number=order_number)
    customer = get_shop_customer(request)
    return render(
        request,
        "shop/order_pending.html",
        {
            "order": order,
            "customer": customer,
        },
    )


# ─── M-Pesa callback (Daraja calls this) ────────────────────
@csrf_exempt
def mpesa_callback(request):
    if request.method != "POST":
        return JsonResponse({"ResultCode": 1, "ResultDesc": "Method not allowed"})
    try:
        data = json.loads(request.body)
        result = mpesa_service.parse_callback(data)

        txn = MpesaTransaction.objects.filter(
            checkout_request_id=result.get("checkout_request_id")
        ).first()

        if txn:
            txn.result_code = result.get("result_code", "")
            txn.result_desc = result.get("result_desc", "")
            txn.raw_callback = data
            if result.get("success"):
                txn.status = MpesaTransaction.STATUS_SUCCESS
                txn.mpesa_receipt = result.get("receipt", "")
                txn.order.payment_status = ShopOrder.PAY_PAID
                txn.order.save()
            else:
                txn.status = MpesaTransaction.STATUS_FAILED
                txn.order.payment_status = ShopOrder.PAY_FAILED
                txn.order.save()
            txn.save()

        return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})
    except Exception as e:
        logger.error(f"M-Pesa callback error: {e}")
        return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})


# ─── payment status polling ──────────────────────────────────
def payment_status(request, order_number):
    order = get_object_or_404(ShopOrder, order_number=order_number)
    return JsonResponse(
        {
            "payment_status": order.payment_status,
            "order_status": order.status,
        }
    )


# ─── retry M-Pesa payment ────────────────────────────────────
@shop_login_required
@require_POST
def retry_payment(request, order_number):
    customer = get_shop_customer(request)
    order = get_object_or_404(ShopOrder, order_number=order_number, customer=customer)
    phone = mpesa_service.format_phone(order.delivery_phone)
    amount = int(order.total_amount)
    result = mpesa_service.stk_push(phone, amount, order.order_number)
    if result.get("success"):
        MpesaTransaction.objects.create(
            order=order,
            phone=phone,
            amount=amount,
            checkout_request_id=result["checkout_request_id"],
            merchant_request_id=result["merchant_request_id"],
        )
        messages.success(request, "M-Pesa prompt sent. Check your phone.")
    else:
        messages.error(request, f'Failed: {result.get("error")}')
    return redirect("shop:order_pending", order_number=order_number)


# ─── customer account ────────────────────────────────────────
@shop_login_required
def my_orders(request):
    customer = get_shop_customer(request)
    orders = ShopOrder.objects.filter(customer=customer).prefetch_related("items")
    return render(
        request, "shop/my_orders.html", {"orders": orders, "customer": customer}
    )


@shop_login_required
def order_detail(request, order_number):
    customer = get_shop_customer(request)
    order = get_object_or_404(ShopOrder, order_number=order_number, customer=customer)
    items = order.items.select_related("product").all()
    txns = order.mpesa_transactions.all()
    return render(
        request,
        "shop/order_detail.html",
        {
            "order": order,
            "items": items,
            "txns": txns,
            "customer": customer,
        },
    )


# ─── admin: manage shop orders ──────────────────────────────
from accounts.decorators import admin_required
from inventory.models import StockMovement
from accounts.middleware import log_action
from accounts.models import AuditLog


@admin_required
def admin_orders(request):
    status = request.GET.get("status", "")
    orders = ShopOrder.objects.select_related(
        "customer", "confirmed_by"
    ).prefetch_related("items")
    if status:
        orders = orders.filter(status=status)
    counts = {
        "pending": ShopOrder.objects.filter(status="pending").count(),
        "confirmed": ShopOrder.objects.filter(status="confirmed").count(),
        "shipped": ShopOrder.objects.filter(status="shipped").count(),
    }
    return render(
        request,
        "shop/admin_orders.html",
        {
            "orders": orders,
            "counts": counts,
            "status_filter": status,
        },
    )


@admin_required
def admin_order_detail(request, order_number):
    order = get_object_or_404(ShopOrder, order_number=order_number)
    items = order.items.select_related("product").all()
    txns = order.mpesa_transactions.all()
    return render(
        request,
        "shop/admin_order_detail.html",
        {
            "order": order,
            "items": items,
            "txns": txns,
        },
    )


@admin_required
@require_POST
def admin_order_action(request, order_number):
    order = get_object_or_404(ShopOrder, order_number=order_number)
    action = request.POST.get("action")

    if action == "confirm" and order.status == ShopOrder.STATUS_PENDING:
        # Check stock for all items
        for item in order.items.select_related("product").all():
            if item.product and item.product.stock_qty < item.quantity:
                messages.error(
                    request,
                    f"Not enough stock for {item.product_name} (have {item.product.stock_qty}, need {item.quantity}).",
                )
                return redirect("shop:admin_order_detail", order_number=order_number)
        # Deduct stock
        for item in order.items.select_related("product").all():
            if item.product:
                before = item.product.stock_qty
                item.product.stock_qty -= item.quantity
                item.product.save()
                StockMovement.objects.create(
                    product=item.product,
                    user=request.user,
                    movement_type=StockMovement.TYPE_SALE,
                    quantity=item.quantity,
                    qty_before=before,
                    qty_after=item.product.stock_qty,
                    reference_id=order.pk,
                    reason=f"Shop order {order.order_number}",
                )
        order.status = ShopOrder.STATUS_CONFIRMED
        order.confirmed_by = request.user
        order.confirmed_at = timezone.now()
        order.save()
        log_action(
            request.user,
            AuditLog.ACTION_UPDATE,
            "ShopOrder",
            order.pk,
            f"Confirmed order {order.order_number} — stock deducted",
            request,
        )
        messages.success(
            request, f"Order {order.order_number} confirmed. Stock updated."
        )

    elif action == "ship" and order.status == ShopOrder.STATUS_CONFIRMED:
        order.status = ShopOrder.STATUS_SHIPPED
        order.save()
        messages.success(request, f"Order {order.order_number} marked as shipped.")

    elif action == "deliver" and order.status == ShopOrder.STATUS_SHIPPED:
        order.status = ShopOrder.STATUS_DELIVERED
        order.save()
        messages.success(request, f"Order {order.order_number} marked as delivered.")

    elif action == "cancel":
        if order.status == ShopOrder.STATUS_CONFIRMED:
            # Return stock
            for item in order.items.select_related("product").all():
                if item.product:
                    before = item.product.stock_qty
                    item.product.stock_qty += item.quantity
                    item.product.save()
                    StockMovement.objects.create(
                        product=item.product,
                        user=request.user,
                        movement_type=StockMovement.TYPE_RETURN,
                        quantity=item.quantity,
                        qty_before=before,
                        qty_after=item.product.stock_qty,
                        reason=f"Cancelled shop order {order.order_number}",
                    )
        order.status = ShopOrder.STATUS_CANCELLED
        order.save()
        messages.warning(request, f"Order {order.order_number} cancelled.")

    return redirect("shop:admin_order_detail", order_number=order_number)
