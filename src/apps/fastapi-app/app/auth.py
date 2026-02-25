"""
Admin Authentication

JWT-based auth using python-jose + passlib.
Credentials and secret are loaded from environment variables:
  ADMIN_USERNAME        — admin username (default: "admin")
  ADMIN_PASSWORD_HASH   — bcrypt hash of the admin password
  ADMIN_JWT_SECRET      — secret key for signing JWTs
  ADMIN_JWT_EXPIRE_MIN  — token lifetime in minutes (default: 480 = 8h)

To generate a password hash:
  python -c "from passlib.context import CryptContext; print(CryptContext(['bcrypt']).hash('yourpassword'))"
"""
import os
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import bcrypt
from jose import JWTError, jwt

_SECRET = os.environ.get("ADMIN_JWT_SECRET", "change-me-in-production")
_ALGORITHM = "HS256"
_EXPIRE_MIN = int(os.environ.get("ADMIN_JWT_EXPIRE_MIN", "480"))

_ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
_ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH", "")

_bearer = HTTPBearer()


def verify_admin_credentials(username: str, password: str) -> bool:
    if username != _ADMIN_USERNAME:
        return False
    if not _ADMIN_PASSWORD_HASH:
        return False
    return bcrypt.checkpw(password.encode(), _ADMIN_PASSWORD_HASH.encode())


def create_access_token() -> str:
    expire = datetime.utcnow() + timedelta(minutes=_EXPIRE_MIN)
    return jwt.encode({"sub": "admin", "exp": expire}, _SECRET, algorithm=_ALGORITHM)


def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> str:
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, _SECRET, algorithms=[_ALGORITHM])
        sub: str = payload.get("sub")
        if sub != "admin":
            raise exc
    except JWTError:
        raise exc
    return sub
