import os
from services.smspool.smspool import SMSPool


sms_pool = SMSPool("https://api.smspool.net/", os.getenv("SMSPOOL_API"))