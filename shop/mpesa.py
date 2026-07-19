"""
Safaricom Daraja M-Pesa STK Push integration.
Docs: https://developer.safaricom.co.ke/APIs/MpesaExpressSimulate

Configure in settings.py:
  MPESA_CONSUMER_KEY
  MPESA_CONSUMER_SECRET
  MPESA_SHORTCODE        (e.g. 174379 for sandbox)
  MPESA_PASSKEY
  MPESA_CALLBACK_URL     (publicly reachable URL, e.g. https://yourdomain.com/shop/mpesa/callback/)
  MPESA_ENV              'sandbox' or 'production'
"""
import base64
import json
import logging
import requests
from datetime import datetime
from django.conf import settings

logger = logging.getLogger(__name__)

SANDBOX_BASE = 'https://sandbox.safaricom.co.ke'
PROD_BASE    = 'https://api.safaricom.co.ke'


def _base_url():
    env = getattr(settings, 'MPESA_ENV', 'sandbox')
    return SANDBOX_BASE if env == 'sandbox' else PROD_BASE


def get_access_token():
    key    = getattr(settings, 'MPESA_CONSUMER_KEY', '')
    secret = getattr(settings, 'MPESA_CONSUMER_SECRET', '')
    url    = f"{_base_url()}/oauth/v1/generate?grant_type=client_credentials"
    try:
        r = requests.get(url, auth=(key, secret), timeout=10)
        r.raise_for_status()
        return r.json().get('access_token')
    except Exception as e:
        logger.error(f"M-Pesa token error: {e}")
        return None


def generate_password():
    shortcode = getattr(settings, 'MPESA_SHORTCODE', '')
    passkey   = getattr(settings, 'MPESA_PASSKEY', '')
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    raw       = f"{shortcode}{passkey}{timestamp}"
    password  = base64.b64encode(raw.encode()).decode()
    return password, timestamp


def stk_push(phone: str, amount: int, order_number: str, description: str = 'GizmoBay Order'):
    """
    Initiates an STK push to the customer's phone.
    phone: format 2547XXXXXXXX
    amount: integer KSh
    Returns dict with checkout_request_id, merchant_request_id on success, or error key.
    """
    token = get_access_token()
    if not token:
        return {'error': 'Could not get M-Pesa access token'}

    password, timestamp = generate_password()
    shortcode    = getattr(settings, 'MPESA_SHORTCODE', '')
    callback_url = getattr(settings, 'MPESA_CALLBACK_URL', '')

    payload = {
        'BusinessShortCode': shortcode,
        'Password':          password,
        'Timestamp':         timestamp,
        'TransactionType':   'CustomerPayBillOnline',
        'Amount':            int(amount),
        'PartyA':            phone,
        'PartyB':            shortcode,
        'PhoneNumber':       phone,
        'CallBackURL':       callback_url,
        'AccountReference':  order_number,
        'TransactionDesc':   description,
    }

    url = f"{_base_url()}/mpesa/stkpush/v1/processrequest"
    try:
        r = requests.post(
            url,
            json=payload,
            headers={'Authorization': f'Bearer {token}'},
            timeout=15,
        )
        data = r.json()
        logger.info(f"STK push response: {data}")
        if data.get('ResponseCode') == '0':
            return {
                'success': True,
                'checkout_request_id': data.get('CheckoutRequestID'),
                'merchant_request_id': data.get('MerchantRequestID'),
            }
        return {'error': data.get('errorMessage', 'STK push failed')}
    except Exception as e:
        logger.error(f"STK push error: {e}")
        return {'error': str(e)}


def parse_callback(data: dict):
    """
    Parse the Daraja STK callback body.
    Returns dict: success, receipt, amount, phone, result_code, result_desc
    """
    try:
        body    = data['Body']['stkCallback']
        rc      = str(body.get('ResultCode', ''))
        desc    = body.get('ResultDesc', '')
        checkout_id  = body.get('CheckoutRequestID', '')
        merchant_id  = body.get('MerchantRequestID', '')
        if rc == '0':
            items = {i['Name']: i['Value'] for i in body.get('CallbackMetadata', {}).get('Item', [])}
            return {
                'success':            True,
                'result_code':        rc,
                'result_desc':        desc,
                'checkout_request_id': checkout_id,
                'merchant_request_id': merchant_id,
                'receipt':            items.get('MpesaReceiptNumber', ''),
                'amount':             items.get('Amount', 0),
                'phone':              str(items.get('PhoneNumber', '')),
            }
        return {
            'success':            False,
            'result_code':        rc,
            'result_desc':        desc,
            'checkout_request_id': checkout_id,
            'merchant_request_id': merchant_id,
        }
    except Exception as e:
        logger.error(f"Callback parse error: {e}")
        return {'success': False, 'result_code': '99', 'result_desc': str(e)}


def format_phone(phone: str) -> str:
    """Normalise to 2547XXXXXXXX."""
    phone = phone.strip().replace(' ', '').replace('-', '')
    if phone.startswith('0'):
        phone = '254' + phone[1:]
    if phone.startswith('+'):
        phone = phone[1:]
    return phone
