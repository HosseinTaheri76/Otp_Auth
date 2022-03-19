import requests
from django.conf import settings


def send_sms(phone, otp):
    url = 'https://api.ghasedak.me/v2/verification/send/simple'
    headers = {'apikey': settings.GHASEDAK_API_KEY}
    body = {
        'receptor': phone,
        'template': '',
        'type': 1,
        'param1': otp
    }
    return requests.post(
        url=url,
        data=body,
        headers=headers
    )
