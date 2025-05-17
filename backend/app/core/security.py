from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hashed version
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hash a password with bcrypt
    """
    return pwd_context.hash(password)

def create_access_token(
    subject: Union[str, Dict[str, Any]], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT token for authentication
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # Convert subject to string if it's not already
    if isinstance(subject, dict):
        subject_data = subject
    else:
        subject_data = {"sub": str(subject)}

    # Add expiration time
    to_encode = subject_data.copy()
    to_encode.update({"exp": expire})
    
    # Create JWT token
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt
