import os
from services.cryptomus.cryptomus import Cryptomus

cryptomus = Cryptomus(merchant_id=os.getenv("CRYPTOMUS_MERCHANT_ID"), api_key=os.getenv("CRYPTOMUS_API"), url_callback=os.getenv("CRYPTOMUS_WEBHOOK_LISTENER"), api_url='https://api.cryptomus.com/v1/')