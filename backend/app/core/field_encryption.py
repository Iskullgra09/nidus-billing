import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


def _fernet() -> Fernet:
    raw = (settings.CREDENTIALS_ENCRYPTION_KEY or "").strip()
    if raw:
        key = raw.encode("utf-8") if len(raw) == 44 else base64.urlsafe_b64encode(
            hashlib.sha256(raw.encode("utf-8")).digest()
        )
    else:
        key = base64.urlsafe_b64encode(
            hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
        )
    return Fernet(key)


def encrypt_bytes(value: bytes) -> bytes:
    return _fernet().encrypt(value)


def encrypt_text(value: str) -> bytes:
    return encrypt_bytes(value.encode("utf-8"))


def decrypt_bytes(token: bytes) -> bytes:
    try:
        return _fernet().decrypt(token)
    except InvalidToken as exc:
        raise ValueError("Unable to decrypt credential payload") from exc


def decrypt_text(token: bytes) -> str:
    return decrypt_bytes(token).decode("utf-8")
