# GizmoBay Stock Management System

A lightweight stock management system for GizmoBay electronics shop, Nairobi.

## Stack
- Django 5 + PostgreSQL
- Bootstrap 5 + vanilla JS
- Runs in browser — no app install needed

---

## Setup (first time)

### 1. Create & activate virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Create PostgreSQL database
```sql
CREATE DATABASE gizmobay_db;
CREATE USER gizmobay_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE gizmobay_db TO gizmobay_user;
```

### 4. Configure environment
Copy `.env.example` to `.env` and fill in your DB credentials.
Then update `gizmobay/settings.py` DB section to read from env, or edit directly.

### 5. Run migrations
```bash
python manage.py migrate
```

### 6. Create admin (shop owner) account
```bash
python manage.py createsuperuser
```
Then open the Django shell and set role to admin:
```bash
python manage.py shell
>>> from accounts.models import User
>>> u = User.objects.get(username='your_username')
>>> u.role = 'admin'
>>> u.save()
```

### 7. Load demo data (optional)
```bash
python manage.py loaddata fixtures/demo.json
```

### 8. Run
```bash
python manage.py runserver
```
Visit: http://127.0.0.1:8000

---

## Roles
| Role   | Can do |
|--------|--------|
| Admin  | Everything — dashboard, reports, purchasing, expenses, users, audit log |
| Worker | New sale (POS), view inventory & customers, view own sales |

## Barcode scanner
- Plug in USB barcode scanner (HID keyboard wedge — no driver needed)
- On the POS screen: scanner adds product to cart automatically
- On Scan Stock-in screen (Admin): scanner updates stock quantity

## Key URLs
| URL | Description |
|-----|-------------|
| `/` | Redirects to dashboard (admin) or POS (worker) |
| `/sales/pos/` | Point-of-sale screen |
| `/inventory/` | Product list |
| `/reports/` | Admin dashboard |
| `/admin/` | Django admin panel |

---

## Marketplace / Shop App

The public-facing shop is at `/shop/` — a separate storefront customers use to browse and order.

### URLs
| URL | Description |
|-----|-------------|
| `/shop/` | Storefront homepage |
| `/shop/product/<id>/` | Product detail |
| `/shop/cart/` | Shopping cart |
| `/shop/checkout/` | Checkout + M-Pesa payment |
| `/shop/register/` | Customer registration |
| `/shop/login/` | Customer login |
| `/shop/my-orders/` | Customer order history |
| `/shop/admin/orders/` | Admin order management panel |

### M-Pesa Setup (Daraja API)

1. Register at https://developer.safaricom.co.ke
2. Create an app → get Consumer Key & Consumer Secret
3. Note your Shortcode and Passkey
4. Update `settings.py`:
   ```python
   MPESA_ENV             = 'production'   # or 'sandbox' for testing
   MPESA_CONSUMER_KEY    = 'your_key'
   MPESA_CONSUMER_SECRET = 'your_secret'
   MPESA_SHORTCODE       = 'your_shortcode'
   MPESA_PASSKEY         = 'your_passkey'
   MPESA_CALLBACK_URL    = 'https://yourdomain.com/shop/mpesa/callback/'
   ```
5. The callback URL **must be publicly reachable** (not localhost). Use ngrok for testing:
   ```bash
   ngrok http 8000
   # Copy the https URL and set as MPESA_CALLBACK_URL
   ```

### Order Flow
```
Customer places order
        ↓
M-Pesa STK push sent to phone
        ↓
Customer enters PIN
        ↓
Daraja calls /shop/mpesa/callback/ → order.payment_status = 'paid'
        ↓
Admin sees order in /shop/admin/orders/ (pending + paid)
        ↓
Admin clicks "Confirm & Deduct Stock" → stock reduced, order = confirmed
        ↓
Admin marks Shipped → Delivered
        ↓
Customer tracks status in My Orders
```

### Sandbox Testing
Use Safaricom test credentials. STK push in sandbox always shows a prompt but
does not require real money. Use phone 254708374149 with PIN 1234 for test payments.
