import qrcode
from io import BytesIO
from .qr_jwt_service import generate_qr_token


# -----------------------------
# GENERATE QR IMAGE
# -----------------------------

def generate_qr(serial: str, tx_hash: str):

    token = generate_qr_token(serial, tx_hash)

    qr = qrcode.make(token)

    buffer = BytesIO()

    qr.save(buffer, format="PNG")

    buffer.seek(0)

    return buffer