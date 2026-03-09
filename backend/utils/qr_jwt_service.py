import jwt
import os
from datetime import datetime

SECRET_KEY = os.getenv("QR_SECRET_KEY", "super_secure_qr_secret")
ALGORITHM = "HS256"


# -----------------------------
# GENERATE JWT TOKEN
# -----------------------------

def generate_qr_token(serial: str, tx_hash: str):

    payload = {
        "serial": serial,
        "tx_hash": tx_hash,
        "iat": datetime.utcnow().timestamp()
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return token


# -----------------------------
# VERIFY JWT TOKEN
# -----------------------------

def verify_qr_token(token: str):

    try:

        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        return decoded

    except jwt.ExpiredSignatureError:

        return None

    except jwt.InvalidTokenError:

        return None