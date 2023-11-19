import requests
from typing import Optional, Dict
from urllib.parse import urlencode



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
    def get_service_list(self) -> dict:
        url = self.construct_url('service/retrieve_all')
        response = requests.post(url)
        print(response.json())
        return response.json()
    