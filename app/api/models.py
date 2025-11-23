"""
Pydantic models for API request and response validation.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """
    Request model for agent query endpoint.
    """
    query: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="User query or prompt for the agent",
        examples=["Calculate compound interest on $1000 at 5% for 10 years"]
    )
    provider: Optional[str] = Field(
        None,
        pattern="^(openai|anthropic)$",
        description="LLM provider to use (openai or anthropic). Uses default if not specified."
    )
    max_tool_calls: Optional[int] = Field(
        None,
        ge=1,
        le=10,
        description="Maximum tool calls allowed for this query. Uses default if not specified."
    )
    correlation_id: Optional[str] = Field(
        None,
        description="Optional correlation ID for request tracking"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What's the weather in New York and how many days until Christmas?",
                "provider": "openai",
                "max_tool_calls": 5
            }
        }


class QueryResponse(BaseModel):
    """
    Response model for agent query endpoint.
    """
    response: str = Field(
        ...,
        description="Agent's final response"
    )
    tool_calls_made: int = Field(
        ...,
        description="Number of tool calls executed"
    )
    provider: str = Field(
        ...,
        description="LLM provider used"
    )
    correlation_id: str = Field(
        ...,
        description="Correlation ID for request tracking"
    )
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        None,
        description="Full conversation history (optional)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "response": "The current weather in New York is 72°F and sunny. Christmas is in 45 days.",
                "tool_calls_made": 2,
                "provider": "openai",
                "correlation_id": "abc-123-def-456"
            }
        }


class ToolInfo(BaseModel):
    """
    Information about a registered tool.
    """
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "calculate_compound_interest",
                "description": "Calculate compound interest on an investment"
            }
        }


class ToolsResponse(BaseModel):
    """
    Response model for tools list endpoint.
    """
    tools: List[ToolInfo] = Field(
        ...,
        description="List of available tools"
    )
    count: int = Field(
        ...,
        description="Total number of tools"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "tools": [
                    {"name": "calculate_compound_interest", "description": "Calculate compound interest"},
                    {"name": "get_weather", "description": "Get weather information"}
                ],
                "count": 2
            }
        }


class HealthResponse(BaseModel):
    """
    Response model for health check endpoint.
    """
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Runtime environment")
    provider: str = Field(..., description="Default LLM provider")
    tools_registered: int = Field(..., description="Number of registered tools")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "environment": "production",
                "provider": "openai",
                "tools_registered": 5
            }
        }


class ErrorResponse(BaseModel):
    """
    Response model for error responses.
    """
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    correlation_id: Optional[str] = Field(None, description="Correlation ID if available")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Query must be between 1 and 5000 characters",
                "correlation_id": "abc-123-def-456"
            }
        }
