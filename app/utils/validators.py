"""
Tool output validators for ensuring data quality and safety.
"""

from typing import Any, Dict, Optional
import re
from datetime import datetime


class ValidationError(Exception):
    """Raised when tool output validation fails."""
    pass


class ToolOutputValidator:
    """
    Validates tool outputs before returning them to the LLM.

    Best Practice: Verify outputs before returning to user (from research requirements)
    """

    @staticmethod
    def validate_numeric(
        value: Any,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
    ) -> float:
        """
        Validate numeric output.

        Args:
            value: Value to validate
            min_value: Minimum allowed value (optional)
            max_value: Maximum allowed value (optional)

        Returns:
            Validated numeric value

        Raises:
            ValidationError: If validation fails
        """
        try:
            num = float(value)
        except (ValueError, TypeError):
            raise ValidationError(f"Expected numeric value, got: {type(value).__name__}")

        if min_value is not None and num < min_value:
            raise ValidationError(f"Value {num} is less than minimum {min_value}")

        if max_value is not None and num > max_value:
            raise ValidationError(f"Value {num} is greater than maximum {max_value}")

        return num

    @staticmethod
    def validate_string(
        value: Any,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None
    ) -> str:
        """
        Validate string output.

        Args:
            value: Value to validate
            min_length: Minimum string length (optional)
            max_length: Maximum string length (optional)
            pattern: Regex pattern to match (optional)

        Returns:
            Validated string value

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(value, str):
            raise ValidationError(f"Expected string, got: {type(value).__name__}")

        if min_length is not None and len(value) < min_length:
            raise ValidationError(f"String length {len(value)} is less than minimum {min_length}")

        if max_length is not None and len(value) > max_length:
            raise ValidationError(f"String length {len(value)} exceeds maximum {max_length}")

        if pattern is not None and not re.match(pattern, value):
            raise ValidationError(f"String does not match pattern: {pattern}")

        return value

    @staticmethod
    def validate_dict(
        value: Any,
        required_keys: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Validate dictionary output.

        Args:
            value: Value to validate
            required_keys: List of required keys (optional)

        Returns:
            Validated dictionary

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(value, dict):
            raise ValidationError(f"Expected dict, got: {type(value).__name__}")

        if required_keys:
            missing_keys = set(required_keys) - set(value.keys())
            if missing_keys:
                raise ValidationError(f"Missing required keys: {missing_keys}")

        return value

    @staticmethod
    def validate_date(value: Any) -> datetime:
        """
        Validate datetime output.

        Args:
            value: Value to validate (string or datetime)

        Returns:
            Validated datetime object

        Raises:
            ValidationError: If validation fails
        """
        if isinstance(value, datetime):
            return value

        if isinstance(value, str):
            try:
                # Try common formats
                for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
                    try:
                        return datetime.strptime(value, fmt)
                    except ValueError:
                        continue
                raise ValueError("No matching format")
            except ValueError:
                raise ValidationError(f"Invalid date format: {value}")

        raise ValidationError(f"Expected date string or datetime, got: {type(value).__name__}")

    @staticmethod
    def sanitize_output(value: Any, max_length: int = 10000) -> Any:
        """
        Sanitize tool output to prevent injection attacks.

        Args:
            value: Value to sanitize
            max_length: Maximum allowed length for strings

        Returns:
            Sanitized value
        """
        if isinstance(value, str):
            # Truncate very long strings
            if len(value) > max_length:
                value = value[:max_length] + "... (truncated)"

            # Remove potential script tags or malicious content
            value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.DOTALL | re.IGNORECASE)

        elif isinstance(value, dict):
            # Recursively sanitize dictionary values
            return {k: ToolOutputValidator.sanitize_output(v, max_length) for k, v in value.items()}

        elif isinstance(value, list):
            # Recursively sanitize list items
            return [ToolOutputValidator.sanitize_output(item, max_length) for item in value]

        return value
