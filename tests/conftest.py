"""
Pytest configuration and shared fixtures.
"""

import pytest
from typing import Generator
from unittest.mock import Mock, MagicMock

from fastapi.testclient import TestClient

from app.main import app
from app.core.agent import ToolAgent
from app.core.providers.base import LLMResponse, ToolCall
from app.tools.registry import ToolRegistry


@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    """
    FastAPI test client fixture.

    Yields:
        TestClient for making API requests
    """
    with TestClient(app) as client:
        yield client


@pytest.fixture
def tool_registry() -> ToolRegistry:
    """
    Empty tool registry fixture.

    Returns:
        Fresh ToolRegistry instance
    """
    return ToolRegistry(enable_validation=True)


@pytest.fixture
def mock_openai_provider() -> Mock:
    """
    Mock OpenAI provider for testing.

    Returns:
        Mocked provider with chat methods
    """
    provider = Mock()

    # Default response: simple text response, no tool calls
    provider.chat.return_value = LLMResponse(
        content="This is a test response",
        tool_calls=[],
        finish_reason="stop",
        raw_response=None
    )

    provider.chat_with_tool_result.return_value = LLMResponse(
        content="Tool result processed",
        tool_calls=[],
        finish_reason="stop",
        raw_response=None
    )

    return provider


@pytest.fixture
def mock_anthropic_provider() -> Mock:
    """
    Mock Anthropic provider for testing.

    Returns:
        Mocked provider with chat methods
    """
    provider = Mock()

    provider.chat.return_value = LLMResponse(
        content="This is a test response from Claude",
        tool_calls=[],
        finish_reason="end_turn",
        raw_response=None
    )

    provider.chat_with_tool_result.return_value = LLMResponse(
        content="Tool result processed by Claude",
        tool_calls=[],
        finish_reason="end_turn",
        raw_response=None
    )

    return provider


@pytest.fixture
def sample_tool_call() -> ToolCall:
    """
    Sample tool call for testing.

    Returns:
        ToolCall instance
    """
    return ToolCall(
        id="call_123",
        name="calculate_compound_interest",
        arguments={
            "principal": 1000.0,
            "rate": 5.0,
            "years": 10
        }
    )


@pytest.fixture
def agent_with_tools(tool_registry: ToolRegistry, mock_openai_provider: Mock) -> ToolAgent:
    """
    Agent fixture with registered tools.

    Args:
        tool_registry: Tool registry fixture
        mock_openai_provider: Mock provider fixture

    Returns:
        ToolAgent instance with tools registered
    """
    from app.tools import financial, data, utilities

    # Register all tools
    tool_registry.register(financial.calculate_compound_interest)
    tool_registry.register(financial.convert_currency)
    tool_registry.register(data.get_weather)
    tool_registry.register(utilities.calculate_date_difference)
    tool_registry.register(utilities.analyze_text)

    # Create agent
    agent = ToolAgent(tool_registry=tool_registry)
    agent.llm_provider = mock_openai_provider

    return agent


@pytest.fixture
def mock_llm_response_with_tool_call(sample_tool_call: ToolCall) -> LLMResponse:
    """
    Mock LLM response that requests a tool call.

    Args:
        sample_tool_call: Sample tool call fixture

    Returns:
        LLMResponse with tool call
    """
    return LLMResponse(
        content=None,
        tool_calls=[sample_tool_call],
        finish_reason="tool_calls",
        raw_response=None
    )


# Test data fixtures
@pytest.fixture
def sample_query() -> str:
    """Sample query for testing."""
    return "Calculate compound interest on $1000 at 5% for 10 years"


@pytest.fixture
def sample_text() -> str:
    """Sample text for text analysis testing."""
    return "Hello world! This is a test. Python is amazing."
