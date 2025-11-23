"""
Main ToolAgent implementation with multi-provider support and loop prevention.

Best Practice: Limit tool calls per turn (max 3-5 to prevent loops)
"""

from typing import Any, Dict, List, Optional
import uuid

from app.config import settings
from app.core.providers import BaseLLMProvider, OpenAIProvider, AnthropicProvider
from app.tools.registry import ToolRegistry, ToolExecutionError
from app.utils.logger import get_logger, bind_correlation_id, unbind_correlation_id

logger = get_logger(__name__)


class ToolAgent:
    """
    Main agent orchestrating LLM interactions and tool execution.

    Features:
    - Multi-provider support (OpenAI, Anthropic)
    - Automatic tool calling with loop prevention
    - Conversation history management
    - Error handling and recovery
    - Correlation ID tracking for debugging
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        max_tool_calls: Optional[int] = None,
        tool_registry: Optional[ToolRegistry] = None,
    ):
        """
        Initialize the ToolAgent.

        Args:
            provider: LLM provider to use ('openai' or 'anthropic'). Defaults to config setting.
            max_tool_calls: Maximum tool calls per turn. Defaults to config setting.
            tool_registry: Optional pre-configured tool registry. Creates new one if not provided.
        """
        # Set provider
        self.provider_name = provider or settings.default_llm_provider
        self.max_tool_calls = max_tool_calls or settings.max_tool_calls_per_turn

        # Initialize LLM provider
        self.llm_provider = self._create_provider(self.provider_name)

        # Initialize or use provided tool registry
        self.tool_registry = tool_registry or ToolRegistry(
            enable_validation=settings.enable_tool_validation
        )

        # Conversation history
        self.messages: List[Dict[str, str]] = []

        logger.info(
            "tool_agent_initialized",
            provider=self.provider_name,
            max_tool_calls=self.max_tool_calls
        )

    def _create_provider(self, provider_name: str) -> BaseLLMProvider:
        """
        Create LLM provider instance.

        Args:
            provider_name: Provider name ('openai' or 'anthropic')

        Returns:
            Initialized provider instance

        Raises:
            ValueError: If provider is unknown
        """
        config = settings.get_provider_config(provider_name)

        if provider_name == "openai":
            return OpenAIProvider(
                api_key=config["api_key"],
                model=config["model"]
            )
        elif provider_name == "anthropic":
            return AnthropicProvider(
                api_key=config["api_key"],
                model=config["model"]
            )
        else:
            raise ValueError(f"Unknown provider: {provider_name}")

    def execute(self, query: str, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a query with automatic tool calling.

        This is the main entry point for agent interactions. It:
        1. Sends query to LLM with available tools
        2. Executes any requested tools
        3. Sends results back to LLM for final response
        4. Prevents infinite loops with max_tool_calls limit

        Args:
            query: User query or prompt
            correlation_id: Optional correlation ID for tracking (auto-generated if not provided)

        Returns:
            Dictionary with response, tool_calls_made, and conversation_history

        Example:
            >>> agent = ToolAgent()
            >>> result = agent.execute("What's 1000 at 5% for 10 years?")
            >>> print(result["response"])
        """
        # Set up correlation ID for request tracking
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        bind_correlation_id(correlation_id)

        try:
            logger.info("agent_execute_started", query=query[:100])

            # Add user query to conversation
            self.messages.append({"role": "user", "content": query})

            # Get tool schemas
            tool_schemas = self.tool_registry.get_schemas()

            # Execute conversation loop with tool calling
            tool_calls_made = 0
            final_response = None

            while tool_calls_made < self.max_tool_calls:
                # Get LLM response
                response = self.llm_provider.chat(
                    messages=self.messages,
                    tools=tool_schemas if tool_schemas else None,
                    temperature=0.7,
                )

                # Check if LLM wants to call tools
                if not response.tool_calls:
                    # No more tool calls, we have final response
                    final_response = response.content
                    self.messages.append({"role": "assistant", "content": final_response})
                    break

                # Execute each tool call
                logger.info("tool_calls_requested", count=len(response.tool_calls))

                # Add assistant message with tool calls
                # (Required for conversation context)
                tool_call_summary = f"Calling {len(response.tool_calls)} tool(s): " + ", ".join(
                    tc.name for tc in response.tool_calls
                )
                self.messages.append({"role": "assistant", "content": tool_call_summary})

                # Execute tools and collect results
                for tool_call in response.tool_calls:
                    tool_calls_made += 1

                    # Check if we've hit the limit
                    if tool_calls_made > self.max_tool_calls:
                        logger.warning(
                            "max_tool_calls_exceeded",
                            max_calls=self.max_tool_calls,
                            attempted=tool_calls_made
                        )
                        final_response = (
                            f"I attempted to use tools to answer your question, but reached "
                            f"the maximum limit of {self.max_tool_calls} tool calls. "
                            f"Please try rephrasing your question or breaking it into smaller parts."
                        )
                        self.messages.append({"role": "assistant", "content": final_response})
                        break

                    try:
                        # Execute tool
                        result = self.tool_registry.execute(
                            tool_name=tool_call.name,
                            arguments=tool_call.arguments,
                        )

                        logger.info(
                            "tool_executed_successfully",
                            tool_name=tool_call.name,
                            result_preview=str(result)[:100]
                        )

                        # Send result back to LLM
                        response = self.llm_provider.chat_with_tool_result(
                            messages=self.messages,
                            tool_call_id=tool_call.id,
                            tool_name=tool_call.name,
                            tool_result=result,
                            tools=tool_schemas,
                        )

                        # Add tool result to conversation
                        result_str = str(result)
                        self.messages.append({
                            "role": "user",
                            "content": f"Tool '{tool_call.name}' returned: {result_str}"
                        })

                        # Check if this is the final response
                        if not response.tool_calls and response.content:
                            final_response = response.content
                            self.messages.append({"role": "assistant", "content": final_response})
                            break

                    except ToolExecutionError as e:
                        # Handle tool execution error
                        error_msg = f"Error executing tool '{tool_call.name}': {str(e)}"
                        logger.error("tool_execution_failed", tool_name=tool_call.name, error=str(e))

                        # Add error to conversation and let LLM handle it
                        self.messages.append({
                            "role": "user",
                            "content": f"Tool execution error: {error_msg}"
                        })

                        # Get LLM to respond to the error
                        response = self.llm_provider.chat(
                            messages=self.messages,
                            tools=None,  # Don't allow more tool calls after error
                        )
                        final_response = response.content
                        self.messages.append({"role": "assistant", "content": final_response})
                        break

                # If we got final response, exit loop
                if final_response:
                    break

            # If we exited without a final response, use last LLM output
            if not final_response:
                final_response = "I apologize, but I was unable to complete your request."

            logger.info(
                "agent_execute_completed",
                tool_calls_made=tool_calls_made,
                response_length=len(final_response)
            )

            return {
                "response": final_response,
                "tool_calls_made": tool_calls_made,
                "conversation_history": self.messages.copy(),
                "correlation_id": correlation_id,
            }

        except Exception as e:
            logger.error("agent_execute_error", error=str(e), exc_info=True)
            raise

        finally:
            unbind_correlation_id()

    def reset_conversation(self) -> None:
        """Clear conversation history."""
        self.messages.clear()
        logger.info("conversation_reset")

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """
        Get conversation history.

        Returns:
            List of message dictionaries
        """
        return self.messages.copy()

    def get_available_tools(self) -> List[Dict[str, str]]:
        """
        Get information about available tools.

        Returns:
            List of tool information dictionaries
        """
        return self.tool_registry.get_tool_info()

    def switch_provider(self, provider_name: str) -> None:
        """
        Switch to a different LLM provider.

        Args:
            provider_name: Provider name ('openai' or 'anthropic')
        """
        self.llm_provider = self._create_provider(provider_name)
        self.provider_name = provider_name
        logger.info("provider_switched", new_provider=provider_name)
