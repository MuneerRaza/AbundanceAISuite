from pydantic import BaseModel, Field
from typing import Optional

# Token schema for authentication
class Token(BaseModel):
    access_token: str
    token_type: str

# Token data for JWT payload
class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None

# Token update schema for admin to adjust user tokens
class TokenUpdate(BaseModel):
    user_id: str
    tokens: int = Field(..., description="Number of tokens to add (positive) or subtract (negative)")
    reason: Optional[str] = None
