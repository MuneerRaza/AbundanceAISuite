from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from bson import ObjectId
from typing import Optional, Dict, Any

from app.core.config import settings
from app.db.mongodb_utils import get_collection, USERS_COLLECTION
from app.db.models import UserRole, UserModel

# OAuth2 password bearer for token validation
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Validate the token and return the current user
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the JWT token
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None: # Added check for user_id
            raise credentials_exception # Added raise
    except JWTError:
        raise credentials_exception # Added raise
    
    # Fetch user from database
    users_collection = await get_collection(USERS_COLLECTION)
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    
    if user is None:
        raise credentials_exception # Added raise
    
    # Check if user is active
    if not user.get("active", True):
        raise HTTPException( # Added raise
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    return user

async def get_current_active_user(current_user: Dict = Depends(get_current_user)) -> Dict:
    """
    Return the current active user
    """
    if not current_user.get("active", True): # This check is somewhat redundant given the check in get_current_user
        raise HTTPException( # Added raise
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive", # Kept for explicitness if called directly in some edge case
        )
    return current_user

async def get_current_admin_user(current_user: Dict = Depends(get_current_user)) -> Dict:
    """
    Check if the current user has admin privileges
    """
    if current_user.get("role") != UserRole.ADMIN:
        raise HTTPException( # Added raise
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user

async def check_token_availability(current_user: Dict = Depends(get_current_active_user)) -> Dict:
    """
    Check if the user has available tokens
    """
    if current_user.get("tokens_remaining", 0) <= 0:
        raise HTTPException( # Added raise
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You have reached your token limit. Please contact an administrator.",
        )
    return current_user
