from .cart import Cart


def shop_context(request):
    cart = Cart(request)
    return {
        'cart': cart,
        'cart_count': len(cart),
        'shop_customer': request.session.get('shop_customer_id'),
    }
