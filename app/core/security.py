import hashlib
import hmac

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_hasher = PasswordHasher()


def hash_password(plain: str) -> str:
    return _hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _hasher.verify(hashed, plain)
    except VerifyMismatchError:
        return False


def credential_version(hashed_password: str) -> str:
    from app.core.config import settings

    return hmac.new(
        settings.secret_key.encode(), hashed_password.encode(), hashlib.sha256
    ).hexdigest()
