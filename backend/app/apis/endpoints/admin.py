from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from bson import ObjectId
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from app.apis.deps import get_current_admin_user
from app.db.mongodb_utils import get_collection, USERS_COLLECTION, TOKEN_USAGE_COLLECTION, DOCUMENTS_COLLECTION, CHAT_SESSIONS_COLLECTION, MESSAGES_COLLECTION
from app.core.security import get_password_hash
from app.services.token_service import add_tokens
from app.schemas.user_schemas import AdminUserCreate, AdminUserUpdate, UserOut
from app.schemas.token_schemas import TokenUpdate
from app.schemas.admin_schemas import AdminDashboardStats, UpdateAnnouncementCreate, UpdateAnnouncementOut, UserStats, TokenUsageStats, StatsPeriod

router = APIRouter()

@router.post("/users", response_model=UserOut)
async def create_user(
    user_data: AdminUserCreate,
    admin_user: Dict = Depends(get_current_admin_user)
):
    """
    Create a new user (admin only)
    """
    users_collection = await get_collection(USERS_COLLECTION)
    
    # Check if user already exists
    existing_user = await users_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user_dict = user_data.dict()
    user_dict["password_hash"] = get_password_hash(user_dict.pop("password"))
    user_dict["created_at"] = datetime.utcnow()
    
    result = await users_collection.insert_one(user_dict)
    created_user = await users_collection.find_one({"_id": result.inserted_id})
    
    return created_user

@router.get("/users", response_model=List[UserOut])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    admin_user: Dict = Depends(get_current_admin_user)
):
    """
    List all users (admin only)
    """
    users_collection = await get_collection(USERS_COLLECTION)
    cursor = users_collection.find().skip(skip).limit(limit)
    return await cursor.to_list(length=limit)

@router.get("/users/{user_id}", response_model=UserOut)
async def get_user(
    user_id: str,
    admin_user: Dict = Depends(get_current_admin_user)
):
    """
    Get a specific user (admin only)
    """
    users_collection = await get_collection(USERS_COLLECTION)
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@router.put("/users/{user_id}", response_model=UserOut)
async def update_user(
    user_id: str,
    user_update: AdminUserUpdate,
    admin_user: Dict = Depends(get_current_admin_user)
):
    """
    Update a user (admin only)
    """
    users_collection = await get_collection(USERS_COLLECTION)
    
    # Check if user exists
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Create update data
    update_data = user_update.dict(exclude_unset=True)
    
    # Hash password if provided
    if "password" in update_data and update_data["password"]:
        update_data["password_hash"] = get_password_hash(update_data.pop("password"))
    
    # Update user
    if update_data:
        await users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
    
    # Return updated user
    updated_user = await users_collection.find_one({"_id": ObjectId(user_id)})
    return updated_user

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    admin_user: Dict = Depends(get_current_admin_user)
):
    """
    Delete a user (admin only)
    """
    users_collection = await get_collection(USERS_COLLECTION)
    
    # Check if user exists
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Cannot delete self
    if str(user["_id"]) == str(admin_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete self"
        )
    
    # Delete user
    await users_collection.delete_one({"_id": ObjectId(user_id)})
    
    return None

@router.post("/tokens", status_code=status.HTTP_200_OK)
async def update_user_tokens(
    token_update: TokenUpdate,
    admin_user: Dict = Depends(get_current_admin_user)
):
    """
    Update a user's token balance (admin only)
    """
    # Apply token update
    success = await add_tokens(
        user_id=token_update.user_id,
        tokens=token_update.tokens,
        admin_id=str(admin_user["_id"]),
        reason=token_update.reason
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or token update failed"
        )
    
    # Get updated token balance
    users_collection = await get_collection(USERS_COLLECTION)
    user = await users_collection.find_one({"_id": ObjectId(token_update.user_id)})
    
    return {"user_id": token_update.user_id, "tokens_remaining": user.get("tokens_remaining", 0)}

@router.get("/stats", response_model=AdminDashboardStats)
async def get_dashboard_stats(
    period: StatsPeriod = StatsPeriod.MONTH,
    admin_user: Dict = Depends(get_current_admin_user)
):
    """
    Get admin dashboard statistics
    """
    # Calculate date ranges based on period
    now = datetime.utcnow()
    if period == StatsPeriod.DAY:
        start_date = now - timedelta(days=1)
    elif period == StatsPeriod.WEEK:
        start_date = now - timedelta(days=7)
    elif period == StatsPeriod.MONTH:
        start_date = now - timedelta(days=30)
    elif period == StatsPeriod.YEAR:
        start_date = now - timedelta(days=365)
    else:  # ALL
        start_date = datetime.min
    
    # Get collections
    users_collection = await get_collection(USERS_COLLECTION)
    token_usage_collection = await get_collection(TOKEN_USAGE_COLLECTION)
    documents_collection = await get_collection(DOCUMENTS_COLLECTION)
    chat_sessions_collection = await get_collection(CHAT_SESSIONS_COLLECTION)
    messages_collection = await get_collection(MESSAGES_COLLECTION)
    
    # User stats
    total_users = await users_collection.count_documents({})
    
    # Active users (users with messages in the period)
    active_user_ids = await messages_collection.distinct(
        "user_id", 
        {"timestamp": {"$gte": start_date}}
    )
    active_users = len(active_user_ids)
    
    # User growth rate (simplified)
    new_users = await users_collection.count_documents({
        "created_at": {"$gte": start_date}
    })
    
    user_growth_rate = (new_users / total_users) * 100 if total_users > 0 else 0
    
    # Token usage stats
    token_usage_pipeline = [
        {"$match": {"timestamp": {"$gte": start_date}}},
        {"$group": {"_id": None, "total": {"$sum": "$tokens_used"}}}
    ]
    token_usage_result = await token_usage_collection.aggregate(token_usage_pipeline).to_list(length=1)
    total_tokens_used = token_usage_result[0]["total"] if token_usage_result else 0
    
    # User breakdown of token usage
    user_breakdown_pipeline = [
        {"$match": {"timestamp": {"$gte": start_date}}},
        {"$group": {"_id": "$user_id", "total": {"$sum": "$tokens_used"}}},
        {"$sort": {"total": -1}},
        {"$limit": 10}  # Top 10 users
    ]
    user_breakdown_result = await token_usage_collection.aggregate(user_breakdown_pipeline).to_list(length=10)
    user_breakdown = {str(item["_id"]): item["total"] for item in user_breakdown_result}
    
    # Daily usage
    daily_usage_pipeline = [
        {"$match": {"timestamp": {"$gte": start_date}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
            "total": {"$sum": "$tokens_used"}
        }},
        {"$sort": {"_id": 1}}
    ]
    daily_usage_result = await token_usage_collection.aggregate(daily_usage_pipeline).to_list(length=100)
    daily_usage = {item["_id"]: item["total"] for item in daily_usage_result}
    
    # Recent uploads and chats
    recent_uploads = await documents_collection.count_documents({
        "upload_date": {"$gte": start_date}
    })
    
    recent_chats = await messages_collection.count_documents({
        "timestamp": {"$gte": start_date}
    })
    
    return {
        "token_usage": {
            "total_tokens_used": total_tokens_used,
            "time_period": period,
            "user_breakdown": user_breakdown,
            "daily_usage": daily_usage
        },
        "user_stats": {
            "total_users": total_users,
            "active_users": active_users,
            "user_growth_rate": user_growth_rate
        },
        "recent_uploads": recent_uploads,
        "recent_chats": recent_chats
    }
