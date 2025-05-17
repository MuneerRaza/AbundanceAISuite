from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List, Any, Optional
from bson import ObjectId

from app.apis.deps import get_current_active_user, check_token_availability
from app.services.llm_service import (
    create_chat_session,
    get_chat_sessions,
    get_chat_messages,
    process_chat_message
)
from app.services.token_service import check_user_tokens
from app.schemas.chat_schemas import (
    ChatSessionCreate,
    ChatSessionUpdate,
    ChatSessionOut,
    MessageCreate,
    MessageOut,
    MessageHistoryRequest,
    ChatCompletionRequest,
    ChatCompletionResponse
)

router = APIRouter()

@router.post("/sessions", response_model=ChatSessionOut)
async def create_new_chat_session(
    session_data: ChatSessionCreate,
    current_user: Dict = Depends(get_current_active_user)
):
    """
    Create a new chat session
    """
    session_id = await create_chat_session(
        user_id=str(current_user["_id"]),
        title=session_data.title
    )
    
    # Get created session details
    sessions = await get_chat_sessions(str(current_user["_id"]))
    created_session = next((s for s in sessions if str(s["_id"]) == session_id), None)
    
    if not created_session:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create chat session"
        )
    
    return created_session

@router.get("/sessions", response_model=List[ChatSessionOut])
async def list_chat_sessions(
    current_user: Dict = Depends(get_current_active_user)
):
    """
    Get all chat sessions for the current user
    """
    return await get_chat_sessions(str(current_user["_id"]))

@router.get("/sessions/{session_id}/messages", response_model=List[MessageOut])
async def get_session_messages(
    session_id: str,
    limit: int = 50,
    skip: int = 0,
    current_user: Dict = Depends(get_current_active_user)
):
    """
    Get messages from a specific chat session
    """
    # Check if the session belongs to the user
    sessions = await get_chat_sessions(str(current_user["_id"]))
    session = next((s for s in sessions if str(s["_id"]) == session_id), None)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    return await get_chat_messages(session_id, limit, skip)

@router.post("/completion", response_model=ChatCompletionResponse)
async def chat_completion(
    request: ChatCompletionRequest,
    current_user: Dict = Depends(check_token_availability)
):
    """
    Send a message and get AI response
    """
    # Check if the session belongs to the user
    sessions = await get_chat_sessions(str(current_user["_id"]))
    session = next((s for s in sessions if str(s["_id"]) == request.chat_session_id), None)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    try:
        # Process the message
        response, message_id, tokens_used = await process_chat_message(
            user_id=str(current_user["_id"]),
            chat_session_id=request.chat_session_id,
            message=request.message,
            system_prompt=request.system_prompt,
            use_rag=request.use_rag
        )
        
        # Get remaining tokens
        remaining_tokens = await check_user_tokens(str(current_user["_id"]))
        
        return {
            "response": response,
            "message_id": message_id,
            "tokens_used": tokens_used,
            "remaining_tokens": remaining_tokens
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating response: {str(e)}"
        )
