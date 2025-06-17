from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class KeyMetadata(BaseModel):
    key_id: str = Field(..., description="Unique identifier for the API key")
    created_at: datetime = Field(..., description="When the key was created")
    last_used: Optional[datetime] = Field(None, description="Last usage timestamp")
    requests_today: int = Field(0, description="Number of requests made today")


class AuthContext(BaseModel):
    api_key: str = Field(..., description="The validated API key")
    metadata: Optional[KeyMetadata] = Field(
        None, description="Key metadata if available"
    )
