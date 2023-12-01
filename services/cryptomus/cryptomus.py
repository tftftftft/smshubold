import requests
import uuid
import hashlib
import base64
import json

from flask import Flask, request, jsonify

from database.methods import firebase_conn

app = Flask(__name__)


# get user_if from order_id 
def get_user_id_from_order_id(order_id: str):
    return order_id.split('_')[0]

# https://api.cryptomus.com/v1/payment
class Cryptomus:
    def __init__(self, merchant_id: str, api_key: str, url_callback: str, api_url: str = 'https://api.cryptomus.com/v1/' ):
        self.merchant_id = merchant_id
        self.api_key = api_key
        self.url_callback = url_callback
        self.api_url = api_url
        
    def _generate_sign(self, data: str):
        return hashlib.md5(base64.b64encode(data.encode()) + self.api_key.encode()).hexdigest()
        
    def construct_order_id(self, user_id: int):
        return f"{user_id}_{uuid.uuid4()}"

            
            
    # {'state': 0, 'result': {'uuid': 'b34afa08-aa01-4644-9ce1-481f17779e8b', 'order_id': '123', 'amount': '10.00',
    # 'payment_amount': None, 'payment_amount_usd': None, 'payer_amount': None, 'payer_amount_exchange_rate': None, 'discount_percent': None,
    # 'discount': '0.00000000', 'payer_currency': None, 'currency': 'USD', 'comments': None, 'merchant_amount': None, 'network': None, 'address': None,
    # 'from': None, 'txid': None, 'payment_status': 'check', 'url': 'https://pay.cryptomus.com/pay/b34afa08-aa01-4644-9ce1-481f17779e8b', 'expired_at': 1701388995,
    # 'status': 'check', 'is_final': False, 'additional_data': None, 'created_at': '2023-12-01T02:03:15+03:00', 'updated_at': '2023-12-01T02:03:15+03:00'}}
    def create_invoice(self, amount: str, currency: str, order_id: str, **kwargs):
        payload = {
            'amount': amount,
            'currency': currency,
            'order_id': self.construct_order_id(order_id),
            'url_callback': self.url_callback,
        }
        payload.update(kwargs)  # Add any additional optional parameters

        sign = self._generate_sign(json.dumps(payload))
        print(sign)
        headers = {
            'merchant': self.merchant_id,
            'sign': sign,
            'Content-Type': 'application/json'
        }
        response = requests.post(self.api_url+'payment', headers=headers, json=payload)
        return response.json()
    
    ### listener for webhooks
    
    
    def verify_webhook_signature(self, received_data: dict) -> bool:
        """
        Verifies the signature of a received webhook.
        
        :param received_data: The data received from the webhook as a dictionary.
        :return: True if the signature is valid, False otherwise.
        """
        received_sign = received_data.pop('sign', None)

        if not received_sign:
            return False

        # Encode the data and generate a new sign
        encoded_data = base64.b64encode(json.dumps(received_data, separators=(',', ':')).encode())
        generated_sign = hashlib.md5(encoded_data + self.api_key.encode()).hexdigest()

        # Compare the generated sign with the received sign
        return generated_sign == received_sign
    
    
    
    # {  "type": "payment",  "uuid": "62f88b36-a9d5-4fa6-aa26-e040c3dbf26d",  "order_id": "97a75bf8eda5cca41ba9d2e104840fcd",  
    # "amount": "3.00000000",  "payment_amount": "3.00000000",  "payment_amount_usd": "0.23",  "merchant_amount": "2.94000000",  
    # "commission": "0.06000000",  "is_final": true,  "status": "paid",  "from": "THgEWubVc8tPKXLJ4VZ5zbiiAK7AgqSeGH",  "wallet_address_uuid": null, 
    # "network": "tron",  "currency": "TRX",  "payer_currency": "TRX",  "additional_data": null,  "convert": {    "to_currency": "USDT", 
    # "commission": null,    "rate": "0.07700000",    "amount": "0.22638000"  },  "txid": "6f0d9c8374db57cac0d806251473de754f361c83a03cd805f74aa9da3193486b", 
    # "sign": "a76c0d77f3e8e1a419b138af04ab600a"}
    def handle_webhook(self):
        @app.route('/webhook', methods=['POST'])
        def webhook_listener():
            """
            Listens for incoming webhooks and verifies their signature.
            """
            if not self.verify_webhook_signature(request.json):
                print('Invalid signature')
                return jsonify({'status': 'error', 'message': 'Invalid signature'}), 403

            # Handle the webhook data here
            print(request.json)
            
            #handle payment type
            if request.json['type'] == 'payment':
                #check if payment is final
                if request.json['status'] == 'paid':
                    # add balance to user
                    user_id = get_user_id_from_order_id(request.json['order_id'])
                    firebase_conn.add_balance(user_id, request.json['amount'])


            return jsonify({'status': 'ok'})
        
        
