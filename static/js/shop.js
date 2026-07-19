// Mobile menu
const mobileMenuBtn = document.getElementById('mobileMenuBtn');
const mobileMenu    = document.getElementById('mobileMenu');
if (mobileMenuBtn) {
  mobileMenuBtn.addEventListener('click', () => mobileMenu.classList.toggle('open'));
}

// CSRF token
function getCookie(name) {
  let v = null;
  document.cookie.split(';').forEach(c => {
    c = c.trim();
    if (c.startsWith(name + '=')) v = decodeURIComponent(c.slice(name.length + 1));
  });
  return v;
}
window.csrfToken = getCookie('csrftoken');

// Add to cart (AJAX)
document.querySelectorAll('.btn-add-cart[data-product-id]').forEach(btn => {
  btn.addEventListener('click', async function(e) {
    e.preventDefault();
    const pid = this.dataset.productId;
    const qty = parseInt(document.querySelector(`#qty-${pid}`)?.value || 1);
    const orig = this.innerHTML;
    this.innerHTML = '<i class="bi bi-hourglass-split"></i> Adding…';
    this.disabled = true;
    try {
      const r = await fetch(`/shop/cart/add/${pid}/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': window.csrfToken, 'X-Requested-With': 'XMLHttpRequest' },
        body: new URLSearchParams({ qty }),
      });
      const data = await r.json();
      if (data.ok) {
        this.innerHTML = '<i class="bi bi-check2"></i> Added!';
        document.querySelectorAll('.cart-badge').forEach(b => { b.textContent = data.count; b.style.display = ''; });
        setTimeout(() => { this.innerHTML = orig; this.disabled = false; }, 1500);
      }
    } catch(e) {
      this.innerHTML = orig; this.disabled = false;
    }
  });
});

// Alert auto-dismiss
document.querySelectorAll('.alert').forEach(el => {
  setTimeout(() => { el.classList.remove('show'); setTimeout(() => el.remove(), 300); }, 5000);
});

// Payment status polling on order pending page
const pollEl = document.getElementById('paymentPollTarget');
if (pollEl) {
  const orderNumber = pollEl.dataset.order;
  let attempts = 0;
  const interval = setInterval(async () => {
    attempts++;
    try {
      const r = await fetch(`/shop/order/${orderNumber}/status/`);
      const data = await r.json();
      if (data.payment_status === 'paid') {
        clearInterval(interval);
        document.getElementById('paymentStatus').innerHTML =
          '<div class="status-icon-wrap status-paid"><i class="bi bi-check-circle-fill"></i></div>' +
          '<h4 class="fw-800">Payment Received!</h4>' +
          '<p class="text-muted mb-4">Your order is now with our team. We will confirm it shortly.</p>';
        document.getElementById('paymentSpinner').style.display = 'none';
      } else if (data.payment_status === 'failed' || attempts >= 24) {
        clearInterval(interval);
        document.getElementById('paymentSpinner').style.display = 'none';
        if (data.payment_status === 'failed') {
          document.getElementById('paymentStatus').innerHTML =
            '<div class="status-icon-wrap status-failed"><i class="bi bi-x-circle-fill"></i></div>' +
            '<h4 class="fw-800">Payment Not Received</h4>' +
            '<p class="text-muted mb-4">We did not receive your payment. You can retry below.</p>';
          document.getElementById('retryBtn')?.removeAttribute('hidden');
        }
      }
    } catch(e) {}
  }, 5000);
}
