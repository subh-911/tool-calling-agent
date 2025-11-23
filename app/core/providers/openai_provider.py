"""
OpenAI provider implementation with native function calling support.
"""

import json
from typing import Any, Dict, List, Optional

from openai import OpenAI
from openai.types.chat import ChatCompletion

from app.core.providers.base import BaseLLMProvider, LLMResponse, ToolCall
from app.utils.logger import get_logger

logger = get_logger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI provider implementation.

    Supports GPT-4 and GPT-3.5 with native function calling.
    """

    def __init__(self, api_key: str, model: str):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            model: Model name (e.g., 'gpt-4-turbo-preview', 'gpt-3.5-turbo')
        """
        super().__init__(api_key, model)
        self.client = OpenAI(api_key=api_key)
        logger.info("openai_provider_initialized", model=model)

    def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """
        Send chat request to OpenAI.

        Args:
            messages: Conversation messages
            tools: Optional tool schemas in OpenAI format
            temperature: Sampling temperature

        Returns:
            LLMResponse with the model's output
        """
        try:
            # Prepare request parameters
            request_params: Dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
            }

            # Add tools if provided
            if tools:
                formatted_tools = self.format_tool_schemas(tools)
                request_params["tools"] = formatted_tools
                request_params["tool_choice"] = "auto"

            logger.debug(
                "openai_chat_request",
                model=self.model,
                message_count=len(messages),
                has_tools=bool(tools)
            )

            # Make API call
            response: ChatCompletion = self.client.chat.completions.create(**request_params)

            # Parse response
            message = response.choices[0].message
            finish_reason = response.choices[0].finish_reason

            # Extract tool calls if present
            tool_calls = []
            if message.tool_calls:
                for tc in message.tool_calls:
                    tool_calls.append(
                        ToolCall(
                            id=tc.id,
                            name=tc.function.name,
                            arguments=json.loads(tc.function.arguments),
                        )
                    )

            logger.info(
                "openai_chat_response",
                finish_reason=finish_reason,
                tool_calls_count=len(tool_calls)
            )

            return LLMResponse(
                content=message.content,
                tool_calls=tool_calls,
                finish_reason=finish_reason,
                raw_response=response,
            )

        except Exception as e:
            logger.error("openai_chat_error", error=str(e), exc_info=True)
            raise

    def chat_with_tool_result(
        self,
        messages: List[Dict[str, str]],
        tool_call_id: str,
        tool_name: str,
        tool_result: Any,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
        """
        Continue conversation with tool execution result.

        Args:
            messages: Previous messages
            tool_call_id: ID of the tool call
            tool_name: Name of the tool
            tool_result: Result from tool execution
            tools: Optional tool schemas

        Returns:
            LLMResponse with the model's final answer
        """
        # Add tool result to messages
        tool_message = {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": json.dumps(tool_result) if not isinstance(tool_result, str) else tool_result,
        }

        messages_with_result = messages + [tool_message]

        logger.debug(
            "openai_chat_with_tool_result",
            tool_name=tool_name,
            tool_call_id=tool_call_id
        )

        # Continue conversation
        return self.chat(messages_with_result, tools=tools)

    def format_tool_schemas(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format tools to OpenAI's expected format.

        OpenAI expects tools in the format:
        {
            "type": "function",
            "function": {
                "name": "...",
                "description": "...",
                "parameters": {...}
            }
        }

        Args:
            tools: Generic tool schemas

        Returns:
            OpenAI-formatted tool schemas
        """
        # Our generic format already matches OpenAI's format
        # No transformation needed
        return tools
