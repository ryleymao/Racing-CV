"""
Pydantic models for data validation and type safety.
Industry standard: Use Pydantic for all data structures.
"""
from pydantic import BaseModel, Field, validator
from typing import Literal, Optional
from datetime import datetime


class SteeringMessage(BaseModel):
    """WebSocket message for steering data."""
    steering: float = Field(..., ge=-1.0, le=1.0, description="Steering value in range [-1, 1]")
    timestamp: Optional[datetime] = None
    
    @validator('steering', pre=True)
    def clamp_steering(cls, v: float) -> float:
        """Ensure steering is in valid range."""
        return max(-1.0, min(1.0, float(v)))
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class GameUpdateMessage(BaseModel):
    """Message sent to game clients."""
    steering: float = Field(..., ge=-1.0, le=1.0)
    timestamp: Optional[datetime] = None


class ConnectionStats(BaseModel):
    """Connection statistics response."""
    game_clients: int = Field(..., ge=0, description="Number of connected game clients")
    cv_clients: int = Field(..., ge=0, description="Number of connected CV clients")
    max_game_clients: int = Field(..., ge=1, description="Maximum allowed game clients")
    max_cv_clients: int = Field(..., ge=1, description="Maximum allowed CV clients")


class HealthResponse(BaseModel):
    """Health check response."""
    status: Literal["healthy", "degraded", "unhealthy"]
    stats: ConnectionStats
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
