from flask import Flask, request, jsonify
from database.methods import firebase_conn
from services.cryptomus.cryptomus_objects import cryptomus
from utilities.utils import get_user_id_from_order_id


# {  "type": "payment",  "uuid": "62f88b36-a9d5-4fa6-aa26-e040c3dbf26d",  "order_id": "97a75bf8eda5cca41ba9d2e104840fcd",  
# "amount": "3.00000000",  "payment_amount": "3.00000000",  "payment_amount_usd": "0.23",  "merchant_amount": "2.94000000",  
# "commission": "0.06000000",  "is_final": true,  "status": "paid",  "from": "THgEWubVc8tPKXLJ4VZ5zbiiAK7AgqSeGH",  "wallet_address_uuid": null, 
# "network": "tron",  "currency": "TRX",  "payer_currency": "TRX",  "additional_data": null,  "convert": {    "to_currency": "USDT", 
# "commission": null,    "rate": "0.07700000",    "amount": "0.22638000"  },  "txid": "6f0d9c8374db57cac0d806251473de754f361c83a03cd805f74aa9da3193486b", 
# "sign": "a76c0d77f3e8e1a419b138af04ab600a"}
        

# {'type': 'payment', 'uuid': '27198cd9-d686-43c1-8305-bfb00915e048', 
# 'order_id': '5258155965_dff6ff4e-f6fa-41ea-be96-8da7889d2165', 'amount': '10.00000000',
# 'payment_amount': '9.99000000', 'payment_amount_usd': '0.00', 'merchant_amount': '9.79838134',
# 'commission': '0.19996696', 'is_final': False, 'status': 'confirm_check', 
# 'from': 'TK84acJWcSncphx4RBKQiNJmx6Bwtg9a8r', 'wallet_address_uuid': None, 'network': 'tron', 
# 'currency': 'USD', 'payer_currency': 'USDT', 'payer_amount': '9.99000000', 
# 'payer_amount_exchange_rate': '1.00016519', 'additional_data': None, 
# 'txid': 'a53ea35fb61510012036946f8ba59c4278a58811f9c8542663bf3d760c1ac9fd'}
app = Flask(__name__)
        
@app.route('/webhook', methods=['POST'])
def webhook_listener():
    """
    Listens for incoming webhooks and verifies their signature.
    """
    if not cryptomus.verify_webhook_signature(request.json):
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