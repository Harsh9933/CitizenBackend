from datetime import datetime, timedelta
from typing import Optional
import hashlib
import base64
import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import get_db
from app.models.models import User
from app.schemas.schemas import TokenData

settings = get_settings()

# HTTP Bearer for token auth
security = HTTPBearer()

# bcrypt has a 72-byte password limit, so we pre-hash with SHA256
def _prepare_password(password: str) -> bytes:
    """Pre-hash password with SHA256 to handle passwords > 72 bytes."""
    return base64.b64encode(
        hashlib.sha256(password.encode('utf-8')).digest()
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    prepared = _prepare_password(plain_password)
    return bcrypt.checkpw(prepared, hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    prepared = _prepare_password(password)
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(prepared, salt).decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[TokenData]:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: int = payload.get("sub")
        role: str = payload.get("role")
        if user_id is None:
            return None
        return TokenData(user_id=user_id, role=role)
    except JWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    print(token)
    token_data = decode_token(token)
    print(token_data)

    if token_data is None or token_data.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.id == token_data.user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user (can add active field check if needed)."""
    return current_user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role for endpoint access."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user