import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET_KEY:     str = os.getenv("JWT_SECRET_KEY", "")
JWT_ALGORITHM:      str = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES:  int = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

if not JWT_SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY is not set. Add it to backend/.env before starting "
        "the server — tokens cannot be signed without it."
    )


class InvalidTokenError(Exception):
    """
    Raised when a token is missing, malformed, expired, or has an
    invalid signature. Caught by the auth dependency and converted
    into an HTTP 401 response.
    """
    pass


# ─── Password Hashing ────────────────────────────────────────

def hash_password(plain_password: str) -> str:
    """
    Hash a plain-text password for storage.

    Uses bcrypt, which generates a random salt per call — hashing the
    same password twice produces two different hashes, which is what
    prevents identical passwords from being visibly identical in the
    database.

    Args:
        plain_password: The user's password, exactly as they typed it.

    Returns:
        A bcrypt hash string, safe to store in the database. Never
        reversible back to the original password.
    """
    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed_bytes.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check a plain-text password against a stored bcrypt hash.

    Args:
        plain_password:  The password submitted at login.
        hashed_password: The hash stored in the database for this user.

    Returns:
        True if the password matches, False otherwise.
    """
    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)


# ─── JWT Tokens ───────────────────────────────────────────────

def create_access_token(user_id: int) -> str:
    """
    Generate a signed JWT proving the bearer is a specific user.

    The token encodes the userId (as "sub", the JWT-standard claim
    name for "subject") and an expiry time. It is signed with
    JWT_SECRET_KEY, so it cannot be edited or forged by a client
    without invalidating the signature.

    Args:
        user_id: The authenticated user's database id.

    Returns:
        An encoded JWT string.
    """
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "exp": expires_at,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> int:
    """
    Verify a JWT and extract the userId it was issued for.

    Args:
        token: The raw JWT string, as sent in the Authorization header.

    Returns:
        The userId encoded in the token.

    Raises:
        InvalidTokenError: If the token is expired, malformed, or its
                           signature doesn't match (i.e. it wasn't
                           issued by this server, or was tampered with).
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as error:
        raise InvalidTokenError("Access token has expired.") from error
    except jwt.InvalidTokenError as error:
        raise InvalidTokenError("Access token is invalid.") from error

    user_id_claim = payload.get("sub")
    if user_id_claim is None:
        raise InvalidTokenError("Access token is missing its subject claim.")

    try:
        return int(user_id_claim)
    except ValueError as error:
        raise InvalidTokenError("Access token subject claim is malformed.") from error
