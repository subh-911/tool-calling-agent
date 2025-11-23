"""
Tool registry for managing and executing tools.

Best Practice: Implement tool validation before returning to user.
"""

from typing import Any, Callable, Dict, List, Optional
import traceback

from app.core.schemas import SchemaGenerator
from app.utils.logger import get_logger
from app.utils.validators import ToolOutputValidator, ValidationError

logger = get_logger(__name__)


class ToolExecutionError(Exception):
    """Raised when tool execution fails."""
    pass


class ToolRegistry:
    """
    Registry for managing tools and their execution.

    Features:
    - Automatic schema generation from Python functions
    - Tool validation before returning results
    - Error handling with detailed logging
    - Support for tool examples
    """

    def __init__(self, enable_validation: bool = True):
        """
        Initialize tool registry.

        Args:
            enable_validation: Enable output validation (recommended)
        """
        self.tools: Dict[str, Callable] = {}
        self.tool_schemas: List[Dict[str, Any]] = []
        self.tool_validators: Dict[str, Optional[Callable]] = {}
        self.enable_validation = enable_validation
        logger.info("tool_registry_initialized", enable_validation=enable_validation)

    def register(
        self,
        func: Callable,
        examples: Optional[List[Dict[str, Any]]] = None,
        validator: Optional[Callable] = None,
    ) -> Callable:
        """
        Register a tool with the registry.

        Args:
            func: Python function to register as a tool
            examples: Optional list of example inputs/outputs for few-shot learning
            validator: Optional custom validation function for outputs

        Returns:
            The original function (allows use as decorator)

        Example:
            >>> registry = ToolRegistry()
            >>> @registry.register
            ... def add(a: int, b: int) -> int:
            ...     '''Add two numbers.'''
            ...     return a + b
        """
        name = func.__name__

        # Generate schema
        schema = SchemaGenerator.generate_schema(func)

        # Add examples if provided (Best Practice: Few-shot examples)
        if examples:
            schema = SchemaGenerator.add_examples_to_schema(schema, examples)

        # Store tool
        self.tools[name] = func
        self.tool_schemas.append(schema)
        self.tool_validators[name] = validator

        logger.info(
            "tool_registered",
            tool_name=name,
            has_examples=bool(examples),
            has_validator=bool(validator)
        )

        return func

    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute a tool with given arguments.

        Args:
            tool_name: Name of the tool to execute
            arguments: Dictionary of arguments to pass

        Returns:
            Tool execution result (validated if validation is enabled)

        Raises:
            ToolExecutionError: If tool execution or validation fails
        """
        if tool_name not in self.tools:
            raise ToolExecutionError(f"Tool '{tool_name}' not found in registry")

        logger.info("tool_execution_started", tool_name=tool_name, arguments=arguments)

        try:
            # Execute tool
            func = self.tools[tool_name]
            result = func(**arguments)

            # Validate output (Best Practice: Verify outputs before returning)
            if self.enable_validation:
                result = self._validate_output(tool_name, result)

            logger.info("tool_execution_succeeded", tool_name=tool_name, result_type=type(result).__name__)
            return result

        except TypeError as e:
            # Handle argument errors
            error_msg = f"Invalid arguments for tool '{tool_name}': {str(e)}"
            logger.error("tool_execution_argument_error", tool_name=tool_name, error=str(e))
            raise ToolExecutionError(error_msg) from e

        except ValidationError as e:
            # Handle validation errors
            error_msg = f"Tool '{tool_name}' output validation failed: {str(e)}"
            logger.error("tool_execution_validation_error", tool_name=tool_name, error=str(e))
            raise ToolExecutionError(error_msg) from e

        except Exception as e:
            # Handle execution errors
            error_msg = f"Tool '{tool_name}' execution failed: {str(e)}\n{traceback.format_exc()}"
            logger.error("tool_execution_error", tool_name=tool_name, error=str(e), exc_info=True)
            raise ToolExecutionError(error_msg) from e

    def _validate_output(self, tool_name: str, output: Any) -> Any:
        """
        Validate tool output.

        Args:
            tool_name: Name of the tool
            output: Output to validate

        Returns:
            Validated (possibly sanitized) output

        Raises:
            ValidationError: If validation fails
        """
        # Use custom validator if provided
        if tool_name in self.tool_validators and self.tool_validators[tool_name]:
            validator = self.tool_validators[tool_name]
            return validator(output)

        # Use default sanitization
        return ToolOutputValidator.sanitize_output(output)

    def get_schemas(self) -> List[Dict[str, Any]]:
        """
        Get all tool schemas.

        Returns:
            List of tool schemas in OpenAI format
        """
        return self.tool_schemas

    def get_tool_names(self) -> List[str]:
        """
        Get all registered tool names.

        Returns:
            List of tool names
        """
        return list(self.tools.keys())

    def get_tool_info(self) -> List[Dict[str, str]]:
        """
        Get summary information about all tools.

        Returns:
            List of dictionaries with tool name and description
        """
        info = []
        for schema in self.tool_schemas:
            func = schema["function"]
            info.append({
                "name": func["name"],
                "description": func["description"],
            })
        return info

    def clear(self) -> None:
        """Clear all registered tools."""
        self.tools.clear()
        self.tool_schemas.clear()
        self.tool_validators.clear()
        logger.info("tool_registry_cleared")
