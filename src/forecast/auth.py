import base64

import jwt
import os
import datetime

def generate_auth_token():

    time_now = datetime.datetime.now()
    expiry_time = time_now + datetime.timedelta(hours=1)

    secret = os.getenv("JWT_SECRET")
    decoded_secret = base64.b64decode(secret)

    payload = {
        "sub": "forecast_service",
        "role": "INTERNAL",
        "iat": time_now,
        "exp": expiry_time,
    }

    token = jwt.encode(payload, decoded_secret, algorithm="HS256")
    return token