from pydantic import BaseModel, Field, EmailStr, HttpUrl
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from bson import ObjectId
from enum import Enum

# Custom Pydantic field for handling MongoDB ObjectId
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
        
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
    
    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

# Role enum for user roles
class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"

# Base model with PyObjectId for MongoDB _id
class MongoBaseModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    
    class Config:
        json_encoders = {ObjectId: str}
        allow_population_by_field_name = True

# User model
class UserModel(MongoBaseModel):
    email: EmailStr
    password_hash: str
    role: UserRole = UserRole.USER
    tokens_remaining: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    full_name: Optional[str] = None
    active: bool = True

# Chat Session model
class ChatSessionModel(MongoBaseModel):
    user_id: PyObjectId
    title: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_archived: bool = False

# Message model
class MessageModel(MongoBaseModel):
    user_id: PyObjectId
    chat_session_id: PyObjectId
    message: str
    response: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tokens_used: int
    metadata: Optional[Dict[str, Any]] = None

# Document model for uploaded files
class DocumentModel(MongoBaseModel):
    filename: str
    original_filename: str
    uploader_id: PyObjectId
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    file_size: int  # in bytes
    file_type: str  # mime type or extension
    local_path: str  # Local filesystem path for development
    vector_store_id: Optional[str] = None  # ID or reference to vector store
    is_embedded: bool = False  # Whether the document has been processed and embedded
    metadata: Optional[Dict[str, Any]] = None

# Update announcement model
class UpdateModel(MongoBaseModel):
    title: str
    summary: str
    document_link: Optional[HttpUrl] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: PyObjectId
    is_active: bool = True

# Token Usage Log model
class TokenUsageLogModel(MongoBaseModel):
    user_id: PyObjectId
    chat_session_id: PyObjectId
    message_id: Optional[PyObjectId] = None
    tokens_used: int
    operation_type: str  # e.g., "chat", "embedding", "admin_adjustment"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None
