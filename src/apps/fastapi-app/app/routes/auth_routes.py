"""
Auth Routes

Provides admin login endpoint.
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.auth import verify_admin_credentials, create_access_token

router = APIRouter(prefix="/admin", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=LoginResponse)
def admin_login(body: LoginRequest):
    """Admin login — returns a JWT on valid credentials."""
    if not verify_admin_credentials(body.username, body.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
        )
    return LoginResponse(access_token=create_access_token())
