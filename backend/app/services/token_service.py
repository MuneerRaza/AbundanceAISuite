from typing import Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

from app.db.mongodb_utils import get_collection, USERS_COLLECTION, TOKEN_USAGE_COLLECTION
from app.core.config import settings

async def check_user_tokens(user_id: str) -> int:
    """
    Get the number of tokens remaining for a user
    """
    users_collection = await get_collection(USERS_COLLECTION)
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    
    if not user:
        return 0
    
    return user.get("tokens_remaining", 0)

async def deduct_tokens(
    user_id: str, 
    tokens: int, 
    operation_type: str,
    chat_session_id: Optional[str] = None,
    message_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Deduct tokens from a user's account and log the usage
    
    Args:
        user_id: User's ID
        tokens: Number of tokens to deduct
        operation_type: Type of operation (e.g., "chat", "embedding")
        chat_session_id: Optional chat session ID
        message_id: Optional message ID
        metadata: Optional metadata about the operation
        
    Returns:
        bool: True if tokens were successfully deducted, False otherwise
    """
    if tokens <= 0:
        return True  # Nothing to deduct
        
    # Get collections
    users_collection = await get_collection(USERS_COLLECTION)
    token_usage_collection = await get_collection(TOKEN_USAGE_COLLECTION)
    
    # Update user's token count
    result = await users_collection.update_one(
        {"_id": ObjectId(user_id), "tokens_remaining": {"$gte": tokens}},
        {"$inc": {"tokens_remaining": -tokens}}
    )
    
    if result.modified_count == 0:
        # Not enough tokens or user not found
        return False
        
    # Log token usage
    log_entry = {
        "user_id": ObjectId(user_id),
        "tokens_used": tokens,
        "operation_type": operation_type,
        "timestamp": datetime.utcnow(),
    }
    
    # Add optional fields if provided
    if chat_session_id:
        log_entry["chat_session_id"] = ObjectId(chat_session_id)
    if message_id:
        log_entry["message_id"] = ObjectId(message_id)
    if metadata:
        log_entry["metadata"] = metadata
        
    await token_usage_collection.insert_one(log_entry)
    
    return True

async def add_tokens(
    user_id: str, 
    tokens: int, 
    admin_id: str,
    reason: Optional[str] = None
) -> bool:
    """
    Add tokens to a user's account (admin operation)
    
    Args:
        user_id: User's ID
        tokens: Number of tokens to add
        admin_id: Admin's ID who authorized the addition
        reason: Optional reason for adding tokens
        
    Returns:
        bool: True if tokens were successfully added, False otherwise
    """
    if tokens <= 0:
        return False  # Must add a positive number of tokens
        
    # Get collections
    users_collection = await get_collection(USERS_COLLECTION)
    token_usage_collection = await get_collection(TOKEN_USAGE_COLLECTION)
    
    # Update user's token count
    result = await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$inc": {"tokens_remaining": tokens}}
    )
    
    if result.modified_count == 0:
        # User not found
        return False
        
    # Log token addition
    log_entry = {
        "user_id": ObjectId(user_id),
        "tokens_used": -tokens,  # Negative to indicate addition
        "operation_type": "admin_adjustment",
        "timestamp": datetime.utcnow(),
        "metadata": {
            "admin_id": admin_id,
            "reason": reason or "Admin token adjustment"
        }
    }
    
    await token_usage_collection.insert_one(log_entry)
    
    return True
