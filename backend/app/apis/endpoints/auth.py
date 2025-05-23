from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta, datetime  # Added datetime
from bson import ObjectId
from typing import Any, Dict, Optional

from app.core.config import settings
from app.core.security import verify_password, get_password_hash, create_access_token
from app.db.mongodb_utils import get_collection, USERS_COLLECTION
from app.db.models import UserModel, UserRole
from app.schemas.user_schemas import UserCreate, UserOut
from app.schemas.token_schemas import Token
from app.apis.deps import get_current_active_user

router = APIRouter()


@router.post("/login", response_model=Token)
async def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Dict[str, Any]:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    # Get users collection
    users_collection = await get_collection(USERS_COLLECTION)

    # Find user by email
    user = await users_collection.find_one({"email": form_data.username})

    # Check if user exists and password is correct
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.get("active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    return {
        "access_token": create_access_token(
            subject=str(user["_id"]),
            expires_delta=access_token_expires,
        ),
        "token_type": "bearer",
    }


@router.post("/signup", response_model=UserOut)
async def create_user(user_data: UserCreate) -> Dict[str, Any]:
    """
    Create new user
    """
    # Get users collection
    users_collection = await get_collection(USERS_COLLECTION)

    # Check if user with the email already exists
    existing_user = await users_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    # Create user object
    user_dict = user_data.model_dump()
    user_dict["password_hash"] = get_password_hash(user_data.password)  # Now stores plain password
    user_dict.pop("password", None)  # Remove plain password field used for creation

    # Set default tokens
    user_dict["tokens_remaining"] = settings.DEFAULT_USER_TOKENS

    # Set role (default is user)
    user_dict["role"] = UserRole.USER

    # Add missing fields required by UserOut response model
    user_dict["created_at"] = datetime.utcnow()
    user_dict["active"] = True  # Default for new users

    # Insert user in the database
    result = await users_collection.insert_one(user_dict)

    # Get created user
    created_user_from_db = await users_collection.find_one({"_id": result.inserted_id})

    if created_user_from_db:
        # Ensure _id is a string for the response model validation
        created_user_from_db["_id"] = str(created_user_from_db["_id"])
        return created_user_from_db
    else:
        # This case should ideally not happen if insert_one was successful
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User created but could not be retrieved."
        )


@router.post("/test-token", response_model=UserOut)
async def test_token(current_user: Dict[str, Any] = Depends(get_current_active_user)) -> Dict[str, Any]:
    """
    Test access token
    """
    # Ensure _id is a string for the response model validation
    if "_id" in current_user and hasattr(current_user["_id"], "__str__"):
        current_user["_id"] = str(current_user["_id"])
    return current_user
