import base64

import jwt
import os
import datetime
from dotenv import load_dotenv

def generate_auth_token():

    time_now = datetime.datetime.now()
    expiry_time = time_now + datetime.timedelta(hours=1)

    load_dotenv()
    secret = ""
    decoded_secret = base64.b64decode(secret)

    payload = {
        "sub": "forecast_service",
        "role": "INTERNAL",
        "iat": time_now,
        "exp": expiry_time,
    }

    token = jwt.encode(payload, decoded_secret, algorithm="HS256")
    return token