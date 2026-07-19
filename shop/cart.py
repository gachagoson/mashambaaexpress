"""
Session-based cart (no DB, no login required to browse).
Stores {product_id: {name, price, qty, image}} in request.session['cart'].
"""
from decimal import Decimal
from inventory.models import Product

CART_SESSION_KEY = 'gizmobay_cart'


class Cart:
    def __init__(self, request):
        self.session = request.session
        self._cart   = self.session.setdefault(CART_SESSION_KEY, {})

    def add(self, product: Product, qty: int = 1, override_qty: bool = False):
        pid = str(product.pk)
        if pid not in self._cart:
            self._cart[pid] = {
                'name':  product.name,
                'price': str(product.retail_price),
                'qty':   0,
                'sku':   product.sku,
                'image': product.image.url if product.image else None,
            }
        if override_qty:
            self._cart[pid]['qty'] = qty
        else:
            self._cart[pid]['qty'] += qty
        # cap at stock
        self._cart[pid]['qty'] = min(self._cart[pid]['qty'], product.stock_qty)
        self.save()

    def remove(self, product_id: int):
        pid = str(product_id)
        if pid in self._cart:
            del self._cart[pid]
            self.save()

    def update(self, product_id: int, qty: int):
        pid = str(product_id)
        if pid in self._cart:
            if qty <= 0:
                self.remove(product_id)
            else:
                self._cart[pid]['qty'] = qty
                self.save()

    def save(self):
        self.session.modified = True

    def clear(self):
        self.session[CART_SESSION_KEY] = {}
        self.session.modified = True

    def __iter__(self):
        pids     = self._cart.keys()
        products = Product.objects.filter(pk__in=pids)
        pmap     = {str(p.pk): p for p in products}
        for pid, item in self._cart.items():
            product = pmap.get(pid)
            if not product:
                continue
            yield {
                'product':  product,
                'name':     item['name'],
                'price':    Decimal(item['price']),
                'qty':      item['qty'],
                'subtotal': Decimal(item['price']) * item['qty'],
                'image':    item.get('image'),
            }

    def __len__(self):
        return sum(i['qty'] for i in self._cart.values())

    def total(self):
        return sum(Decimal(i['price']) * i['qty'] for i in self._cart.values())
