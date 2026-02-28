from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ResearchRequest(BaseModel):
    """Request model for research endpoint"""
    query: str = Field(..., description="User's research query")
    session_id: Optional[str] = Field(None, description="Session identifier")


class ResearchResponse(BaseModel):
    """Response model for research endpoint"""
    response: str = Field(..., description="Final synthesized answer")
    session_id: str = Field(..., description="Session identifier")
    plan: Optional[str] = Field(None, description="Research plan created")
    sources: List[str] = Field(default_factory=list, description="Sources consulted")
    success: bool = Field(..., description="Whether the request was successful")
    error: Optional[str] = Field(None, description="Error message if failed")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    version: str = Field(default="2.0.0")


class ConversationHistoryResponse(BaseModel):
    """Response model for conversation history"""
    session_id: str
    messages: List[Dict[str, Any]]
    count: int


class WebhookRequest(BaseModel):
    """Request from n8n webhook"""
    query: str
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class WebhookResponse(BaseModel):
    """Response to n8n webhook"""
    response: str
    session_id: str
    plan: Optional[str] = None
    sources: List[str] = []
    success: bool
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Optional[Dict[str, Any]] = None