"""
FastAPI route handlers for the Tool-Calling Agent API.
"""

from typing import Optional
import uuid

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.api.models import (
    QueryRequest,
    QueryResponse,
    ToolsResponse,
    ToolInfo,
    HealthResponse,
    ErrorResponse,
)
from app.config import settings
from app.core.agent import ToolAgent
from app.tools.registry import ToolRegistry, ToolExecutionError
from app.tools import financial, data, utilities
from app.utils.logger import get_logger
from app import __version__

logger = get_logger(__name__)

# Create router
router = APIRouter(prefix=settings.api_v1_prefix)

# Initialize global tool registry
tool_registry = ToolRegistry(enable_validation=settings.enable_tool_validation)

# Register all tools with examples
tool_registry.register(
    financial.calculate_compound_interest,
    examples=[
        {"input": {"principal": 1000, "rate": 5, "years": 10}, "output": {"final_amount": 1628.89}},
        {"input": {"principal": 5000, "rate": 7.5, "years": 5}, "output": {"final_amount": 7229.31}},
    ]
)

tool_registry.register(
    financial.convert_currency,
    examples=[
        {"input": {"amount": 100, "from_currency": "USD", "to_currency": "EUR"}, "output": {"converted_amount": 92.50}},
    ]
)

tool_registry.register(
    data.get_weather,
    examples=[
        {"input": {"city": "New York"}, "output": {"temperature": 22, "condition": "sunny"}},
    ]
)

tool_registry.register(
    utilities.calculate_date_difference,
    examples=[
        {"input": {"start_date": "2024-01-01", "end_date": "2024-12-31"}, "output": {"days": 365}},
    ]
)

tool_registry.register(
    utilities.analyze_text,
    examples=[
        {"input": {"text": "Hello world!"}, "output": {"word_count": 2, "sentence_count": 1}},
    ]
)

logger.info("tools_registered", count=len(tool_registry.get_tool_names()))


@router.post(
    "/query",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute agent query",
    description="Send a query to the agent and get a response with automatic tool calling",
    responses={
        200: {"description": "Successful response"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    }
)
async def query_agent(request: QueryRequest) -> QueryResponse:
    """
    Execute a query with the tool-calling agent.

    The agent will:
    1. Analyze the query to determine if tools are needed
    2. Automatically call relevant tools
    3. Synthesize results into a natural language response

    Args:
        request: Query request with query text and optional parameters

    Returns:
        Agent response with answer and execution metadata
    """
    correlation_id = request.correlation_id or str(uuid.uuid4())

    try:
        logger.info(
            "query_received",
            query_preview=request.query[:100],
            provider=request.provider,
            correlation_id=correlation_id
        )

        # Create agent instance
        agent = ToolAgent(
            provider=request.provider,
            max_tool_calls=request.max_tool_calls,
            tool_registry=tool_registry,
        )

        # Execute query
        result = agent.execute(
            query=request.query,
            correlation_id=correlation_id
        )

        # Build response
        response = QueryResponse(
            response=result["response"],
            tool_calls_made=result["tool_calls_made"],
            provider=agent.provider_name,
            correlation_id=correlation_id,
            conversation_history=result.get("conversation_history"),
        )

        logger.info("query_completed", correlation_id=correlation_id)
        return response

    except ToolExecutionError as e:
        logger.error("query_tool_error", error=str(e), correlation_id=correlation_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error="ToolExecutionError",
                message=str(e),
                correlation_id=correlation_id
            ).model_dump()
        )

    except ValueError as e:
        logger.error("query_validation_error", error=str(e), correlation_id=correlation_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error="ValidationError",
                message=str(e),
                correlation_id=correlation_id
            ).model_dump()
        )

    except Exception as e:
        logger.error("query_unexpected_error", error=str(e), correlation_id=correlation_id, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="InternalServerError",
                message="An unexpected error occurred. Please try again.",
                correlation_id=correlation_id
            ).model_dump()
        )


@router.get(
    "/tools",
    response_model=ToolsResponse,
    status_code=status.HTTP_200_OK,
    summary="List available tools",
    description="Get information about all registered tools"
)
async def list_tools() -> ToolsResponse:
    """
    Get list of all available tools.

    Returns:
        List of tools with their names and descriptions
    """
    tools_info = tool_registry.get_tool_info()
    tools = [ToolInfo(**info) for info in tools_info]

    return ToolsResponse(
        tools=tools,
        count=len(tools)
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check service health and configuration"
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns:
        Service status and configuration information
    """
    return HealthResponse(
        status="healthy",
        version=__version__,
        environment=settings.environment,
        provider=settings.default_llm_provider,
        tools_registered=len(tool_registry.get_tool_names())
    )
