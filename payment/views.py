from django.shortcuts import render
from django.utils import timezone
from pathlib import Path
from django.shortcuts import redirect
import os
import uuid
import environ
import json
import hmac
import hashlib
import base64
import requests


BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

def request(request):
    if request.method == "POST":
        url = f"{env('LINE_SANDBOX_URL')}{env('LINE_REQUEST_URL')}"
        order_id = f"order_{str(uuid.uuid4())}"
        package_id = f"package_{str(uuid.uuid4())}"

        payload = {
            'amount': 100,
            'currency': 'TWD',
            'orderId': order_id,
            'packages': [{
                'id': package_id,
                'amount': 100,
                'products': [{
                    'id': '1',
                    'name': '測試商品',
                    'quantity': 1,
                    'price': 100,
                }]
            }],
            'redirectUrls': {
                'confirmUrl': f"https://{env('HOSTNAME')}/payment/confirm",
                'cancelUrl': f"https://{env('HOSTNAME')}/payment/cancel"
            }
        }

        signature_uri = env('LINE_SIGNATURE_REQUEST_URI')        
        headers = create_headers(payload, signature_uri)
        body = json.dumps(payload)

        response = requests.post(url, headers=headers, data=body)
        
        if response.status_code == 200:
            data = response.json()
            if data['returnCode'] == '0000':
                return redirect(data['info']['paymentUrl']['web'])
            else:
                print(data['returnMessage'])
                return render(request, "payment/checkout.html")
        else:
            print(f'Error: {response.status_code}')
            return render(request, "payment/checkout.html")
    else:
        return render(request, "payment/checkout.html")

def confirm(request):
    transaction_id = request.GET.get('transactionId')
    url = f"{env('LINE_SANDBOX_URL')}/v3/payments/{transaction_id}/confirm"
    order_id = request.GET.get('orderId')

    payload = {
        'amount': 100,
        'currency': 'TWD',
    }

    signature_uri = f"/v3/payments/{transaction_id}/confirm"
    headers = create_headers(payload, signature_uri)

    body = json.dumps(payload)
    response = requests.post(url, headers=headers, data=body)
    
    data = response.json()
    if data['returnCode'] == '0000':
        return render(request, "payment/success.html")
    else:
        print(data['returnMessage'])
        return render(request, "payment/fail.html")

def success(request):
    return render(request, "payment/success.html")

def fail(request):
    return render(request, "payment/fail.html")

def create_headers(body, uri):
    channel_id = env('LINE_CHANNEL_ID')
    nonce = str(uuid.uuid4())
    secret_key = env('LINE_CHANNEL_SECRET_KEY')
    body_to_json = json.dumps(body)
    message = secret_key + uri + body_to_json + nonce

    binary_message = message.encode()
    binary_secret_key = secret_key.encode()

    hash = hmac.new(binary_secret_key, binary_message, hashlib.sha256)

    signature = base64.b64encode(hash.digest()).decode()

    headers = {
      'Content-Type': 'application/json',
      'X-LINE-ChannelId': channel_id,
      'X-LINE-Authorization-Nonce': nonce,
      'X-LINE-Authorization': signature
    }

    return headers