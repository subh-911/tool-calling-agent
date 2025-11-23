"""
Automatic tool schema generation from Python functions.

This module inspects Python functions and generates OpenAI-compatible
tool schemas automatically.
"""

import inspect
from typing import Any, Callable, Dict, get_type_hints, Optional


class SchemaGenerator:
    """
    Generates tool schemas from Python functions.

    Best Practice: Rich tool descriptions are critical (40% accuracy improvement)
    """

    @staticmethod
    def generate_schema(func: Callable) -> Dict[str, Any]:
        """
        Generate OpenAI-compatible tool schema from a Python function.

        Extracts:
        - Function name
        - Docstring (description + parameter docs)
        - Parameter types and defaults
        - Required vs optional parameters

        Args:
            func: Python function to generate schema for

        Returns:
            Tool schema in OpenAI format

        Example:
            >>> def add(a: int, b: int) -> int:
            ...     '''Add two numbers together.
            ...     Args:
            ...         a: First number
            ...         b: Second number
            ...     '''
            ...     return a + b
            >>> schema = SchemaGenerator.generate_schema(add)
        """
        name = func.__name__
        docstring = inspect.getdoc(func) or "No description available"
        signature = inspect.signature(func)

        # Extract type hints
        type_hints = get_type_hints(func)

        # Parse docstring for parameter descriptions
        param_descriptions = SchemaGenerator._parse_docstring_params(docstring)

        # Extract main description (everything before Args:)
        description = docstring.split("Args:")[0].strip()
        if not description:
            description = f"Execute {name} function"

        # Build parameters schema
        parameters = {
            "type": "object",
            "properties": {},
            "required": [],
        }

        for param_name, param in signature.parameters.items():
            # Skip self/cls parameters
            if param_name in ("self", "cls"):
                continue

            # Get type information
            param_type = SchemaGenerator._python_type_to_json_schema(
                type_hints.get(param_name, Any)
            )

            # Get parameter description from docstring
            param_desc = param_descriptions.get(param_name, f"{param_name} parameter")

            # Add to properties
            parameters["properties"][param_name] = {
                "type": param_type,
                "description": param_desc,
            }

            # Mark as required if no default value
            if param.default == inspect.Parameter.empty:
                parameters["required"].append(param_name)

        return {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            },
        }

    @staticmethod
    def _parse_docstring_params(docstring: str) -> Dict[str, str]:
        """
        Parse parameter descriptions from docstring.

        Supports Google-style docstrings:
        Args:
            param_name: Description here
            another_param: Another description

        Args:
            docstring: Function docstring

        Returns:
            Dictionary mapping parameter names to descriptions
        """
        param_descriptions = {}

        if "Args:" not in docstring:
            return param_descriptions

        # Extract Args section
        args_section = docstring.split("Args:")[1]
        if "Returns:" in args_section:
            args_section = args_section.split("Returns:")[0]
        if "Example:" in args_section:
            args_section = args_section.split("Example:")[0]

        # Parse each parameter
        lines = args_section.strip().split("\n")
        current_param = None
        current_desc = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if this is a new parameter (contains ':')
            if ":" in line and not line.startswith(" "):
                # Save previous parameter if exists
                if current_param:
                    param_descriptions[current_param] = " ".join(current_desc).strip()

                # Start new parameter
                parts = line.split(":", 1)
                current_param = parts[0].strip()
                current_desc = [parts[1].strip()] if len(parts) > 1 else []
            else:
                # Continuation of previous description
                if current_param:
                    current_desc.append(line)

        # Save last parameter
        if current_param:
            param_descriptions[current_param] = " ".join(current_desc).strip()

        return param_descriptions

    @staticmethod
    def _python_type_to_json_schema(python_type: type) -> str:
        """
        Convert Python type to JSON schema type.

        Args:
            python_type: Python type annotation

        Returns:
            JSON schema type string
        """
        # Handle common types
        type_mapping = {
            int: "integer",
            float: "number",
            str: "string",
            bool: "boolean",
            list: "array",
            dict: "object",
        }

        # Get the origin type (handles Optional, List, etc.)
        origin = getattr(python_type, "__origin__", None)
        if origin is not None:
            python_type = origin

        return type_mapping.get(python_type, "string")

    @staticmethod
    def add_examples_to_schema(
        schema: Dict[str, Any],
        examples: list[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Add few-shot examples to tool schema.

        Best Practice: Use few-shot examples in tool descriptions
        to show example inputs/outputs.

        Args:
            schema: Existing tool schema
            examples: List of example dictionaries with 'input' and 'output' keys

        Returns:
            Schema with examples added to description

        Example:
            >>> examples = [
            ...     {"input": {"a": 5, "b": 3}, "output": 8},
            ...     {"input": {"a": 10, "b": 7}, "output": 17}
            ... ]
            >>> schema = add_examples_to_schema(schema, examples)
        """
        if not examples:
            return schema

        # Build examples section
        examples_text = "\n\nExamples:\n"
        for i, example in enumerate(examples, 1):
            examples_text += f"{i}. Input: {example['input']} → Output: {example['output']}\n"

        # Append to description
        schema["function"]["description"] += examples_text

        return schema
