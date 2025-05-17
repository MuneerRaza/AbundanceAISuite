from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from app.apis.deps import get_current_active_user
from app.db.mongodb_utils import get_collection, USERS_COLLECTION
from app.core.security import get_password_hash
from app.schemas.user_schemas import UserUpdate, UserOut

router = APIRouter()

@router.get("/me", response_model=UserOut)
async def read_user_me(
    current_user: Dict = Depends(get_current_active_user)
):
    """
    Get current user profile
    """
    # Ensure _id is a string for the response model validation
    if "_id" in current_user and hasattr(current_user["_id"], "__str__"):
        current_user["_id"] = str(current_user["_id"])
    return current_user

@router.put("/me", response_model=UserOut)
async def update_user_me(
    user_update: UserUpdate,
    current_user: Dict = Depends(get_current_active_user)
):
    """
    Update current user profile
    """
    users_collection = await get_collection(USERS_COLLECTION)
      # Create update data
    update_data = user_update.model_dump(exclude_unset=True, exclude={"role", "tokens_remaining"})
    
    # Hash password if provided
    if "password" in update_data and update_data["password"]:
        update_data["password_hash"] = get_password_hash(update_data["password"])
        del update_data["password"]
    
    # Update user
    if update_data:
        await users_collection.update_one(
            {"_id": current_user["_id"]},
            {"$set": update_data}
        )
    
    # Return updated user
    updated_user = await users_collection.find_one({"_id": current_user["_id"]})
    # Ensure _id is a string for the response model validation
    if updated_user and "_id" in updated_user and hasattr(updated_user["_id"], "__str__"):
        updated_user["_id"] = str(updated_user["_id"])
    return updated_user

@router.get("/tokens", response_model=Dict[str, int])
async def get_remaining_tokens(
    current_user: Dict = Depends(get_current_active_user)
):
    """
    Get remaining tokens for current user
    """
    return {"tokens_remaining": current_user.get("tokens_remaining", 0)}
