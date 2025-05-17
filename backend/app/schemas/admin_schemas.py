from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

from app.schemas.user_schemas import UserOut

# Stats time period enum
class StatsPeriod(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
    ALL = "all"

# Usage statistics schema
class TokenUsageStats(BaseModel):
    total_tokens_used: int
    time_period: StatsPeriod
    user_breakdown: Optional[Dict[str, int]] = None
    daily_usage: Optional[Dict[str, int]] = None

# User Statistics
class UserStats(BaseModel):
    total_users: int
    active_users: int
    user_growth_rate: float  # Percentage

# Admin dashboard stats
class AdminDashboardStats(BaseModel):
    token_usage: TokenUsageStats
    user_stats: UserStats
    recent_uploads: int
    recent_chats: int
    
# Update announcement create schema
class UpdateAnnouncementCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    summary: str = Field(..., min_length=1)
    document_link: Optional[str] = None

# Update announcement output schema
class UpdateAnnouncementOut(BaseModel):
    id: str = Field(..., alias="_id")
    title: str
    summary: str
    document_link: Optional[str] = None
    created_at: datetime
    created_by: str
    is_active: bool
    
    class Config:
        allow_population_by_field_name = True

# Admin system info schema
class SystemInfo(BaseModel):
    app_version: str
    environment: str
    mongodb_status: str
    vector_store_status: str
    groq_api_status: str
