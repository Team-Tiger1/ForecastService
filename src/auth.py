import os
import base64
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import InvalidTokenError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load the secret from environment variables
RAW_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "").strip()

# Fallback secret if the real one cannot be loaded
if not RAW_SECRET_KEY:
    RAW_SECRET_KEY = "bWV0YWxzb21ldGltZXNlbnNleW91b3RoZXJzaGlubmluZ2JyZWFrcG9wdWxhdGlvbnM="

# Adding '=' to the secret key if it is not a multiple of 4 to make it a multiple of 4
padded_key = RAW_SECRET_KEY + "=" * ((4 - len(RAW_SECRET_KEY) % 4) % 4)

try:
    # Decode the Base64 key into bytes
    SECRET_KEY = base64.b64decode(padded_key)
except Exception as e:
    raise

ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_current_vendor_id(token: str = Depends(oauth2_scheme)):
    """
    FastAPI Dependency to validate the JWT string and extract the vendor ID.
    :param token: The JWT string.
    :return: The vendor ID.
    :raises: HTTPException 401 if the token is invalid.
             HttpException 403 if the token cannot be pulled from environment variables.
             HTTPException 422 if the token is valid but does not contain a vendor ID.
    """

    # If the secret cannot be pulled from the environment variables raise HttpException 403
    if RAW_SECRET_KEY == "secret":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="JWT Token Not Being Pulled from environment variables"
        )

    try:
        # Decode token and verify signature
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        vendor_id: str = payload.get("sub")

        # Check the token contains a vendor ID
        if vendor_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Token is valid, but it has no User ID inside it."
            )
        return vendor_id

    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Auth Failed: Invalid token or signature",
            headers={"WWW-Authenticate": "Bearer"},
        )