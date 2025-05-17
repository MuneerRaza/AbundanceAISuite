from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Chat session creation schema
class ChatSessionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)

# Chat session update schema
class ChatSessionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    is_archived: Optional[bool] = None

# Chat session output schema
class ChatSessionOut(BaseModel):
    id: str = Field(..., alias="_id")
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    is_archived: bool
    
    class Config:
        allow_population_by_field_name = True

# Message creation schema
class MessageCreate(BaseModel):
    message: str = Field(..., min_length=1)
    chat_session_id: str
    metadata: Optional[Dict[str, Any]] = None

# Message output schema
class MessageOut(BaseModel):
    id: str = Field(..., alias="_id")
    user_id: str
    chat_session_id: str
    message: str
    response: str
    timestamp: datetime
    tokens_used: int
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        allow_population_by_field_name = True

# Message history request schema
class MessageHistoryRequest(BaseModel):
    chat_session_id: str
    limit: int = 50
    skip: int = 0

# Chat completion request schema
class ChatCompletionRequest(BaseModel):
    chat_session_id: str
    message: str = Field(..., min_length=1)
    system_prompt: Optional[str] = None
    use_rag: bool = True
    metadata: Optional[Dict[str, Any]] = None

# Chat completion response schema
class ChatCompletionResponse(BaseModel):
    response: str
    message_id: str
    tokens_used: int
    remaining_tokens: int
