"""
Anthropic provider implementation with Claude 3+ tool use support.
"""

import json
from typing import Any, Dict, List, Optional

from anthropic import Anthropic

from app.core.providers.base import BaseLLMProvider, LLMResponse, ToolCall
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic provider implementation.

    Supports Claude 3+ models with tool use (function calling).
    """

    def __init__(self, api_key: str, model: str):
        """
        Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key
            model: Model name (e.g., 'claude-3-5-sonnet-20241022')
        """
        super().__init__(api_key, model)
        self.client = Anthropic(api_key=api_key)
        logger.info("anthropic_provider_initialized", model=model)

    def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """
        Send chat request to Anthropic.

        Args:
            messages: Conversation messages
            tools: Optional tool schemas
            temperature: Sampling temperature

        Returns:
            LLMResponse with the model's output
        """
        try:
            # Convert messages to Anthropic format
            anthropic_messages = self._convert_messages(messages)

            # Prepare request parameters
            request_params: Dict[str, Any] = {
                "model": self.model,
                "messages": anthropic_messages,
                "max_tokens": 4096,
                "temperature": temperature,
            }

            # Add tools if provided
            if tools:
                formatted_tools = self.format_tool_schemas(tools)
                request_params["tools"] = formatted_tools

            logger.debug(
                "anthropic_chat_request",
                model=self.model,
                message_count=len(anthropic_messages),
                has_tools=bool(tools)
            )

            # Make API call
            response = self.client.messages.create(**request_params)

            # Parse response
            content_text = ""
            tool_calls = []

            for block in response.content:
                if block.type == "text":
                    content_text += block.text
                elif block.type == "tool_use":
                    tool_calls.append(
                        ToolCall(
                            id=block.id,
                            name=block.name,
                            arguments=block.input,
                        )
                    )

            logger.info(
                "anthropic_chat_response",
                stop_reason=response.stop_reason,
                tool_calls_count=len(tool_calls)
            )

            return LLMResponse(
                content=content_text if content_text else None,
                tool_calls=tool_calls,
                finish_reason=response.stop_reason,
                raw_response=response,
            )

        except Exception as e:
            logger.error("anthropic_chat_error", error=str(e), exc_info=True)
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
        # Convert messages to Anthropic format
        anthropic_messages = self._convert_messages(messages)

        # Add tool use block to the last assistant message
        # This is required by Anthropic's API
        if anthropic_messages and anthropic_messages[-1]["role"] == "assistant":
            if "content" not in anthropic_messages[-1]:
                anthropic_messages[-1]["content"] = []

            # Ensure content is a list
            if isinstance(anthropic_messages[-1]["content"], str):
                anthropic_messages[-1]["content"] = [
                    {"type": "text", "text": anthropic_messages[-1]["content"]}
                ]

            # Add tool use block
            anthropic_messages[-1]["content"].append({
                "type": "tool_use",
                "id": tool_call_id,
                "name": tool_name,
                "input": {},
            })

        # Add tool result as user message
        tool_result_str = json.dumps(tool_result) if not isinstance(tool_result, str) else tool_result

        anthropic_messages.append({
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_call_id,
                    "content": tool_result_str,
                }
            ]
        })

        logger.debug(
            "anthropic_chat_with_tool_result",
            tool_name=tool_name,
            tool_call_id=tool_call_id
        )

        # Continue conversation
        return self.chat(anthropic_messages, tools=tools)

    def format_tool_schemas(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format tools to Anthropic's expected format.

        Anthropic expects tools in the format:
        {
            "name": "...",
            "description": "...",
            "input_schema": {...}
        }

        Args:
            tools: Generic tool schemas (OpenAI format)

        Returns:
            Anthropic-formatted tool schemas
        """
        anthropic_tools = []

        for tool in tools:
            # Convert from OpenAI format to Anthropic format
            if tool.get("type") == "function":
                func = tool["function"]
                anthropic_tools.append({
                    "name": func["name"],
                    "description": func["description"],
                    "input_schema": func.get("parameters", {
                        "type": "object",
                        "properties": {},
                    }),
                })

        return anthropic_tools

    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Convert generic messages to Anthropic format.

        Anthropic doesn't support 'system' role in messages array,
        it's passed separately. Also handles tool messages.

        Args:
            messages: Generic message format

        Returns:
            Anthropic-formatted messages
        """
        anthropic_messages = []

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")

            # Skip system messages (should be passed as system parameter)
            if role == "system":
                continue

            # Handle tool messages (convert to user role)
            if role == "tool":
                # Tool results are added as user messages in Anthropic
                continue

            # Add regular messages
            anthropic_messages.append({
                "role": role,
                "content": content,
            })

        return anthropic_messages
