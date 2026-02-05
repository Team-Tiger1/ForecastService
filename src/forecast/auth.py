import os
import base64
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from dotenv import load_dotenv

load_dotenv()

secret_env = os.getenv("JWT_SECRET_KEY", "defaultJWTSECRETKEYFORTESTING2543676897jiohu")

try:
    SECRET_KEY = base64.b64decode(secret_env)
except Exception:
    SECRET_KEY = secret_env

ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_vendor_id(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        vendor_id: str = payload.get("sub")
        if vendor_id is None:
            raise credentials_exception
        return vendor_id
    except JWTError:
        raise credentials_exception