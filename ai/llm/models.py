"""
Pydantic models for LLM module
"""

from typing import Dict, Any
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Chat message model"""
    role: str = Field(..., description="Message role (system, user, assistant)")
    content: str = Field(..., description="Message content")


class CompletionResponse(BaseModel):
    """Response model for LLM completion"""
    content: str = Field(..., description="Generated content")
    provider: str = Field(..., description="LLM provider used")
    model: str = Field(..., description="Model used")
    usage: Dict[str, Any] = Field(..., description="Token usage information")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")