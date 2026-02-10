import os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from dotenv import load_dotenv
import base64

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")


if not SECRET_KEY:
    print("Not pulling jwt secret from enviornment variables ")
    #Randomly Genorated Base 64
    SECRET_KEY = "bWV0YWxzb21ldGltZXNlbnNleW91b3RoZXJzaGlubmluZ2JyZWFrcG9wdWxhdGlvbnM="

SECRET_KEY = base64.b64decode(SECRET_KEY.encode())

ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_current_vendor_id(token: str = Depends(oauth2_scheme)):

    if(SECRET_KEY == "secret"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="JWT Token Not Being Pulled from enviornment variables"
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        vendor_id: str = payload.get("sub")

        if vendor_id is None:
            print("Vendor_id is null")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Token is valid, but it has no User ID inside it."
            )
        return vendor_id

    except JWTError as e:
        print(e)
        print("JWTERROR")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Auth Failed: {str(e)}"
        )