from django.shortcuts import render
from django.utils import timezone
from pathlib import Path
from django.shortcuts import redirect
import os
import uuid
import json
import hmac
import hashlib
import base64
import requests
import environ
import time


BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Create your views here.

def index(request):
    return render(request, "payment/index.html")

def request(request):
    if request.method == "POST":
        uri = env('LINE_REQUEST_URL')
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
                'confirmUrl': '',
                'cancelUrl': ''
            }
        }
        
        header = create_header(payload)
        body = json.dumps(payload)

        response = requests.post(uri, headers=header, data=body)

        if response.status_code == 200:
            data = response.json()
            if data['returnCode'] == '0000':
                return redirect(data['info']['paymentUrl']['web'])
            else:
                print(data['returnMessage'])
        else:
            print(f'Error: {response.status_code}')

    else:
        return render(request, "payment/checkout.html")


def create_header(body):
    channel_id = env('LINE_CHANNEL_ID')
    secret_key = env('LINE_CHANNEL_SECRET_KEY')
    uri = env('LINE_SIGNATURE_REQUEST_URI')
    nonce = str(uuid.uuid4())
    body_to_json = json.dumps(body)
    message = secret_key + uri + body_to_json + nonce

    binary_message = message.encode()
    binary_secret_key = secret_key.encode()
    
    hash = hmac.new(binary_secret_key, binary_message, hashlib.sha256)

    signature = base64.b64encode(hash.digest()).decode()

    header = {
      'Content-Type': 'application/json',
      'X-LINE-ChannelId': channel_id,
      'X-LINE-Authorization-Nonce': nonce,
      'X-LINE-Authorization': signature
    }

    return header
