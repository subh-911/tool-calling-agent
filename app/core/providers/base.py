"""
Base abstract provider for LLM integrations.

Uses the Strategy pattern to allow easy switching between different LLM providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ToolCall:
    """
    Represents a tool call requested by the LLM.

    Attributes:
        id: Unique identifier for the tool call
        name: Name of the tool to call
        arguments: Dictionary of arguments for the tool
    """
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class LLMResponse:
    """
    Unified response format from any LLM provider.

    Attributes:
        content: Text content of the response (if any)
        tool_calls: List of tool calls requested (if any)
        finish_reason: Reason the model stopped generating
        raw_response: Original response from the provider
    """
    content: Optional[str]
    tool_calls: List[ToolCall]
    finish_reason: str
    raw_response: Any


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All provider implementations must inherit from this class
    and implement the required methods.
    """

    def __init__(self, api_key: str, model: str):
        """
        Initialize the provider.

        Args:
            api_key: API key for the provider
            model: Model identifier to use
        """
        self.api_key = api_key
        self.model = model

    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """
        Send a chat request to the LLM.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            tools: Optional list of tool schemas
            temperature: Sampling temperature (0.0 to 1.0)

        Returns:
            LLMResponse object with the model's response

        Raises:
            Exception: If the API call fails
        """
        pass

    @abstractmethod
    def chat_with_tool_result(
        self,
        messages: List[Dict[str, str]],
        tool_call_id: str,
        tool_name: str,
        tool_result: Any,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
        """
        Continue conversation after tool execution.

        Args:
            messages: Previous conversation messages
            tool_call_id: ID of the executed tool call
            tool_name: Name of the executed tool
            tool_result: Result from the tool execution
            tools: Optional list of tool schemas

        Returns:
            LLMResponse object with the model's response
        """
        pass

    @abstractmethod
    def format_tool_schemas(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format tool schemas to the provider's expected format.

        Args:
            tools: Generic tool schema list

        Returns:
            Provider-specific formatted tool schemas
        """
        pass

    def validate_connection(self) -> bool:
        """
        Validate that the provider connection is working.

        Returns:
            True if connection is valid, False otherwise
        """
        try:
            # Simple test message
            response = self.chat(
                messages=[{"role": "user", "content": "Hello"}],
                temperature=0.0,
            )
            return response is not None
        except Exception:
            return False
