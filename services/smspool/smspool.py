import requests
from typing import Optional, Dict
from urllib.parse import urlencode
from enum import Enum




class Pricing_Options(Enum):
    LOWEST = 0
    HIGHEST = 1
    
class Rent_Days(Enum):
    DAY = 1
    WEEK = 7
    FIFTEEN_DAYS = 15
    MONTH = 30
    
pricing_options = Pricing_Options
rent_days = Rent_Days
    
class SMSPool:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        
        
    def construct_url(self, endpoint: str, params: Optional[Dict[str, str]] = None) -> str:
        url = self.base_url + endpoint
        if params:
            query_string = urlencode(params)
            url += '?' + query_string
        print(url)
        return url
    
    # POST https://api.smspool.net/service/retrieve_all
    async def get_service_list(self) -> dict:
        url = self.construct_url('service/retrieve_all')
        try:
            response = requests.post(url)
            # print(response.json())
            return response.json()
        except Exception as e:
            print(e)
            return None
    
    #curl --location 'https://api.smspool.net/request/price' --form 'key="98EIv8oI4SBsBF0Nmow1x1Wwiz8xqRoA"' --form 'country="US"' --form 'service="Facebook"' --form 'pool="1"'
    async def get_service_price(self, country: str, service: str) -> dict:
        url = self.construct_url('request/price', params={'key': self.api_key, 'country': country, 'service': service, 'pool': 0})
        try:
            response = requests.post(url)
            # print(response.json())
            return response.json()
        except Exception as e:
            print(e)
            return None
    
    #     curl --location 'https://api.smspool.net/purchase/sms' \
    # --form 'key="Your API key"' \
    # --form 'country="US"' \
    # --form 'service="Facebook"' \
    # --form 'pricing_option="0"' \ Set to 0 if you'd like the cheapest numbers, set to 1 for highest success rate
    # --form 'quantity=""' \ Quantity of numbers ordered
    # --form 'create_token=""' Optional param; set to 1 if you'd like to create a token link that anyone can access.
    # --form 'areacode="[702, 725, 775]"' \
    async def order_sms(self, country: str, service: str, pricing_option: int, quantity: int, areacodes: dict, create_token: int) -> dict:
        url = self.construct_url('purchase/sms', params={'key': self.api_key, 'country': country, 'service': service, 'pricing_option': pricing_option, 'quantity': quantity, 'areacode': areacodes, 'create_token': create_token})
        response = requests.post(url, timeout=30)
        print(response.json())
        return response.json()

    #     curl --location 'https://api.smspool.net/sms/cancel' \
    # --form 'orderid=""' \
    # --form 'key="Your API key"'
    
    def cancel_sms(self, orderid: str) -> dict:
        url = self.construct_url('sms/cancel', params={'key': self.api_key, 'orderid': orderid})
        try:
            response = requests.post(url)
            print(response.json())
            return response.json()
        except Exception as e:
            print(e)
            return None
    
    
    #     curl --location 'https://api.smspool.net/sms/check' \
    # --form 'orderid=""' \
    # --form 'key="Your API key"'
    
    async def check_sms(self, orderid: str) -> dict:
        url = self.construct_url('sms/check', params={'key': self.api_key, 'orderid': orderid})
        try:
            response = requests.post(url)
            print(response.json())
            return response.json()
        except Exception as e:
            print(e)
            return None
    
    # Resend
    # Resend the order. Keep in mind that some pools will have a charge per resend.

    # Responses
    # | Success | {"success":1,"message":"Number has been requested again","resend":0} |
    # | Fail | {"success":0,"message":"Phonenumber could not be requested again, try later again.","resend":0} |
    #     curl --location 'https://api.smspool.net/sms/resend' \
    # --form 'orderid=""' \
    # --form 'key="Your API key"'
    
    #     curl --location 'https://api.smspool.net/sms/cancel' \
    # --form 'orderid=""' \
    # --form 'key="Your API key"'
    async def resend(self, orderid: str) -> dict:
        url = self.construct_url('sms/resend', params={'key': self.api_key, 'orderid': orderid})
        try:
            response = requests.post(url, timeout=5)
            print(response.json())
            return response.json()
        except Exception as e:
            print(e)
            return None
    

    
    ########################################
    #RENTALS
    
    #     curl --location 'https://api.smspool.net/rental/retrieve_all' \
    # --form 'key="Your API key"' \
    # --form 'type="0 | 1"'  Choose whether the rental is extendable or not with a 0 or 1
    async def retrive_rentals_extendable(self) -> dict:
        url = self.construct_url('rental/retrieve_all', params={'key': self.api_key, 'type': 1})
        try:
            response = requests.post(url)
            print(response.json())
            return response.json()
        except Exception as e:
            print(e)
            return None
        
        
    async def retrive_rentals_not_extendable(self) -> dict:
        url = self.construct_url('rental/retrieve_all', params={'key': self.api_key, 'type': 0})
        try:
            response = requests.post(url)
            print(response.json())
            return response.json()
        except Exception as e:
            print(e)
            return None
            
            
    #     curl --location 'https://api.smspool.net/purchase/rental' \
    # --form 'key="Your API key"' \
    # --form 'id="1"' \ Rental ID retrieved from Retrieve Rental IDs
    # --form 'days="30"' \
    # --form 'service_id=""' Optional value on which service you'd purchase the rental for
    async def order_rental(self, id: int, days: Rent_Days, service_id: Optional[int] = None) -> dict:
        url = self.construct_url('purchase/rental', params={'key': self.api_key, 'id': id, 'days': days, 'service_id': service_id})
        try:
            response = requests.post(url)
            print(response.json())
            return response.json()
        except Exception as e:
            print(e)
            return None
    
    #response example:
    # {'success': 1, 'message': 'You have ordered a rental, it will be issued instantly.', 'phonenumber': '16809101906', 'days': 30, 'rental_code': '7xabp0RL', 'expiry': 1703552020}
    
    #order any service rental - order_rental(6, 30)
    #order service not listed rental - order_rental(7, 30, 817)
    #order specific service rental - order_rental(7, 30, X)
    
    #     curl --location 'https://api.smspool.net/rental/extend' \
    # --form 'key="Your API key"' \
    # --form 'days="30"' \
    # --form 'rental_code=""' The retrieved rental code from the Order rental endpoint.
    def extend_rental(self, days: Rent_Days, rental_code: str) -> dict:
        url = self.construct_url('rental/extend', params={'key': self.api_key, 'days': days, 'rental_code': rental_code})
        response = requests.post(url)
        print(response.json())
        return response.json()
    
    #     curl --location 'https://api.smspool.net/rental/auto_extend' \
    # --form 'key="Your API key"' \
    # --form 'rental_code=""' The retrieved rental code from the Order rental endpoint.
    def enable_auto_extend_rental(self, rental_code: str) -> dict:
        url = self.construct_url('rental/auto_extend', params={'key': self.api_key, 'rental_code': rental_code})
        response = requests.post(url)
        print(response.json())
        return response.json()
    
    #     curl --location 'https://api.smspool.net/rental/retrieve_messages' \
    # --form 'key="Your API key"' \
    # --form 'rental_code=""'
    async def retrive_rental_messages(self, rental_code: str) -> dict:
        url = self.construct_url('rental/retrieve_messages', params={'key': self.api_key, 'rental_code': rental_code})
        try:
            response = requests.post(url)
            print(response.json())
            return response.json()
        except Exception as e:
            print(e)
            return None
            
    #     curl --location 'https://api.smspool.net/rental/retrieve_status' \
    # --form 'key="Your API key"' \
    # --form 'rental_code=""'
    async def retrive_rental_status(self, rental_code: str) -> dict:
        url = self.construct_url('rental/retrieve_status', params={'key': self.api_key, 'rental_code': rental_code})
        try:
            response = requests.post(url, timeout=5)
            print(response.json())
            return response.json()
        except Exception as e:
            print(e)
            return None
    
        #     curl --location 'https://api.smspool.net/rental/retrieve' \
        # --form 'key="Your API key"'
    def retrive_active_rentals(self) -> dict:
        url = self.construct_url('rental/retrieve', params={'key': self.api_key})
        response = requests.post(url)
        print(response.json())
        return response.json()


    

    
    
    
    
    
    