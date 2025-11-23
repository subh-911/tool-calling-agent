"""
Tests for the core ToolAgent functionality.
"""

import pytest
from unittest.mock import Mock, patch

from app.core.agent import ToolAgent
from app.core.providers.base import LLMResponse, ToolCall
from app.tools.registry import ToolRegistry


class TestToolAgent:
    """Tests for ToolAgent class."""

    def test_agent_initialization(self, tool_registry):
        """Test agent initialization."""
        with patch('app.core.agent.OpenAIProvider'):
            agent = ToolAgent(
                provider="openai",
                tool_registry=tool_registry
            )

            assert agent.provider_name == "openai"
            assert agent.tool_registry is tool_registry

    def test_agent_simple_query_no_tools(self, mock_openai_provider):
        """Test agent with simple query that doesn't need tools."""
        with patch('app.core.agent.OpenAIProvider', return_value=mock_openai_provider):
            agent = ToolAgent(provider="openai")

            result = agent.execute("Hello, how are you?")

            assert "response" in result
            assert result["tool_calls_made"] == 0
            assert mock_openai_provider.chat.called

    def test_agent_with_tool_call(self, agent_with_tools, mock_openai_provider):
        """Test agent executing a tool call."""
        # First response: request tool call
        tool_call = ToolCall(
            id="call_123",
            name="calculate_compound_interest",
            arguments={"principal": 1000, "rate": 5, "years": 10}
        )

        mock_openai_provider.chat.return_value = LLMResponse(
            content=None,
            tool_calls=[tool_call],
            finish_reason="tool_calls",
            raw_response=None
        )

        # Second response: final answer after tool execution
        mock_openai_provider.chat_with_tool_result.return_value = LLMResponse(
            content="The final amount would be $1628.89",
            tool_calls=[],
            finish_reason="stop",
            raw_response=None
        )

        agent_with_tools.llm_provider = mock_openai_provider

        result = agent_with_tools.execute("Calculate interest on $1000 at 5% for 10 years")

        assert result["tool_calls_made"] == 1
        assert "response" in result
        assert mock_openai_provider.chat_with_tool_result.called

    def test_agent_multiple_tool_calls(self, agent_with_tools, mock_openai_provider):
        """Test agent with multiple sequential tool calls."""
        call_count = 0

        def mock_chat(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                # First call: request weather tool
                return LLMResponse(
                    content=None,
                    tool_calls=[ToolCall(
                        id="call_1",
                        name="get_weather",
                        arguments={"city": "New York"}
                    )],
                    finish_reason="tool_calls",
                    raw_response=None
                )
            else:
                # Final response
                return LLMResponse(
                    content="Weather retrieved successfully",
                    tool_calls=[],
                    finish_reason="stop",
                    raw_response=None
                )

        mock_openai_provider.chat.side_effect = mock_chat
        mock_openai_provider.chat_with_tool_result.return_value = LLMResponse(
            content="The weather in New York is sunny",
            tool_calls=[],
            finish_reason="stop",
            raw_response=None
        )

        agent_with_tools.llm_provider = mock_openai_provider

        result = agent_with_tools.execute("What's the weather in New York?")

        assert result["tool_calls_made"] == 1

    def test_agent_max_tool_calls_prevention(self, agent_with_tools, mock_openai_provider):
        """Test that agent prevents infinite loops with max_tool_calls."""
        # Always request more tool calls (simulating a loop)
        mock_openai_provider.chat.return_value = LLMResponse(
            content=None,
            tool_calls=[ToolCall(
                id="call_loop_1",
                name="get_weather",
                arguments={"city": "New York"}
            )],
            finish_reason="tool_calls",
            raw_response=None
        )

        mock_openai_provider.chat_with_tool_result.return_value = LLMResponse(
            content=None,
            tool_calls=[ToolCall(
                id="call_loop_2",
                name="get_weather",
                arguments={"city": "New York"}
            )],
            finish_reason="tool_calls",
            raw_response=None
        )

        agent_with_tools.llm_provider = mock_openai_provider
        agent_with_tools.max_tool_calls = 3  # Set low limit for testing

        result = agent_with_tools.execute("What's the weather?")

        # Should stop at max_tool_calls (verify loop prevention is working)
        assert result["tool_calls_made"] <= 3
        assert result["response"] is not None
        assert len(result["response"]) > 0

    def test_agent_tool_execution_error_handling(self, agent_with_tools, mock_openai_provider):
        """Test agent handles tool execution errors gracefully."""
        # Request a tool call with invalid arguments
        mock_openai_provider.chat.return_value = LLMResponse(
            content=None,
            tool_calls=[ToolCall(
                id="call_123",
                name="calculate_compound_interest",
                arguments={"principal": -1000, "rate": 5, "years": 10}  # Invalid: negative
            )],
            finish_reason="tool_calls",
            raw_response=None
        )

        # After error, provide final response
        mock_openai_provider.chat.side_effect = [
            mock_openai_provider.chat.return_value,
            LLMResponse(
                content="I encountered an error with the calculation",
                tool_calls=[],
                finish_reason="stop",
                raw_response=None
            )
        ]

        agent_with_tools.llm_provider = mock_openai_provider

        result = agent_with_tools.execute("Calculate interest on -$1000")

        assert "response" in result
        # Should have attempted 1 tool call
        assert result["tool_calls_made"] == 1

    def test_agent_conversation_history(self, agent_with_tools, mock_openai_provider):
        """Test that agent maintains conversation history."""
        agent_with_tools.llm_provider = mock_openai_provider

        result = agent_with_tools.execute("Hello")

        assert len(result["conversation_history"]) > 0
        assert result["conversation_history"][0]["role"] == "user"
        assert result["conversation_history"][0]["content"] == "Hello"

    def test_agent_reset_conversation(self, agent_with_tools):
        """Test conversation reset."""
        agent_with_tools.messages = [
            {"role": "user", "content": "test"},
            {"role": "assistant", "content": "response"}
        ]

        agent_with_tools.reset_conversation()

        assert len(agent_with_tools.messages) == 0

    def test_agent_get_available_tools(self, agent_with_tools):
        """Test getting available tools list."""
        tools = agent_with_tools.get_available_tools()

        assert len(tools) == 5
        assert all("name" in tool for tool in tools)
        assert all("description" in tool for tool in tools)

    def test_agent_switch_provider(self):
        """Test switching between providers."""
        with patch('app.core.agent.OpenAIProvider') as mock_openai:
            with patch('app.core.agent.AnthropicProvider') as mock_anthropic:
                agent = ToolAgent(provider="openai")

                assert agent.provider_name == "openai"

                agent.switch_provider("anthropic")

                assert agent.provider_name == "anthropic"
                mock_anthropic.assert_called()

    def test_agent_correlation_id(self, agent_with_tools, mock_openai_provider):
        """Test correlation ID tracking."""
        agent_with_tools.llm_provider = mock_openai_provider

        correlation_id = "test-correlation-123"
        result = agent_with_tools.execute("Test query", correlation_id=correlation_id)

        assert result["correlation_id"] == correlation_id

    def test_agent_auto_generates_correlation_id(self, agent_with_tools, mock_openai_provider):
        """Test that correlation ID is auto-generated if not provided."""
        agent_with_tools.llm_provider = mock_openai_provider

        result = agent_with_tools.execute("Test query")

        assert "correlation_id" in result
        assert len(result["correlation_id"]) > 0
