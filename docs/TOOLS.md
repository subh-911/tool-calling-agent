# Tool Creation Guide

Complete guide for creating and registering custom tools with the Tool-Calling Agent.

## Overview

Tools are Python functions that the LLM can automatically execute to answer user queries. The agent handles:
- Automatic schema generation from function signatures
- Type validation and conversion
- Output validation and sanitization
- Error handling and recovery

## Quick Start

### Basic Tool Example

```python
def calculate_sum(a: int, b: int) -> int:
    """
    Add two numbers together.

    Args:
        a: First number to add
        b: Second number to add

    Returns:
        Sum of a and b

    Examples:
        1. Input: {"a": 5, "b": 3} → Output: 8
        2. Input: {"a": 10, "b": 20} → Output: 30
    """
    return a + b

# Register the tool
tool_registry.register(calculate_sum)
```

That's it! The agent will automatically:
1. Generate an OpenAI-compatible schema
2. Extract parameter descriptions from docstring
3. Handle type validation
4. Make it available to the LLM

## Best Practices

### 1. Rich Descriptions (Critical for Accuracy)

**Research shows 40% accuracy improvement with good descriptions.**

```python
# ❌ Poor description
def weather(city: str) -> dict:
    """Get weather."""
    pass

# ✅ Good description
def get_weather(city: str, units: str = "celsius") -> dict:
    """
    Get current weather information for a specified city.

    This tool retrieves comprehensive weather data including temperature,
    conditions, humidity, and wind speed. Use this when users ask about
    current weather, temperature, or atmospheric conditions.

    Args:
        city: Name of the city (e.g., 'New York', 'London', 'Tokyo')
        units: Temperature units - 'celsius' or 'fahrenheit' (default: celsius)

    Returns:
        Dictionary with temperature, condition, humidity, wind_speed

    Examples:
        1. Input: {"city": "New York"} → Output: {"temperature": 72, "condition": "sunny"}
        2. Input: {"city": "London", "units": "celsius"} → Output: {"temperature": 15, "condition": "rainy"}
    """
    pass
```

### 2. Include Examples in Docstrings

Examples help the LLM understand expected inputs and outputs.

```python
"""
Examples:
    1. Input: {"principal": 1000, "rate": 5, "years": 10} → Output: {"final_amount": 1628.89}
    2. Input: {"principal": 5000, "rate": 7.5, "years": 5} → Output: {"final_amount": 7229.31}
"""
```

### 3. Use Type Hints

Type hints enable automatic validation:

```python
from typing import Dict, List, Optional

def analyze_data(
    data: List[float],
    threshold: Optional[float] = None
) -> Dict[str, float]:
    """Analyze numerical data."""
    pass
```

### 4. Validate Inputs

Use the built-in validators:

```python
from app.utils.validators import ToolOutputValidator

def calculate_interest(principal: float, rate: float) -> dict:
    """Calculate interest."""
    # Validate inputs
    principal = ToolOutputValidator.validate_numeric(
        principal,
        min_value=0.01,
        max_value=1000000000
    )
    rate = ToolOutputValidator.validate_numeric(
        rate,
        min_value=0.0,
        max_value=100.0
    )

    # ... calculation logic
    return result
```

### 5. Return Structured Data

Always return dictionaries with clear keys:

```python
# ❌ Poor return value
def calculate_interest(principal, rate, years):
    return principal * (1 + rate/100) ** years

# ✅ Good return value
def calculate_interest(principal, rate, years):
    final_amount = principal * (1 + rate/100) ** years
    return {
        "final_amount": round(final_amount, 2),
        "interest_earned": round(final_amount - principal, 2),
        "principal": principal,
        "years": years,
        "annual_rate": rate
    }
```

## Tool Registration

### Basic Registration

```python
from app.tools.registry import ToolRegistry

registry = ToolRegistry()

# Method 1: Direct registration
registry.register(my_tool_function)

# Method 2: As decorator
@registry.register
def my_tool():
    """Tool description."""
    pass
```

### Registration with Examples

```python
registry.register(
    calculate_compound_interest,
    examples=[
        {"input": {"principal": 1000, "rate": 5, "years": 10}, "output": {"final_amount": 1628.89}},
        {"input": {"principal": 5000, "rate": 7.5, "years": 5}, "output": {"final_amount": 7229.31}}
    ]
)
```

### Registration with Custom Validator

```python
def validate_weather_output(output):
    """Custom validator for weather tool."""
    required_keys = ["temperature", "condition", "humidity"]
    return ToolOutputValidator.validate_dict(output, required_keys=required_keys)

registry.register(
    get_weather,
    validator=validate_weather_output
)
```

## Complete Tool Example

Here's a production-ready tool with all best practices:

```python
from typing import Dict
from app.utils.validators import ToolOutputValidator

def calculate_mortgage_payment(
    loan_amount: float,
    annual_rate: float,
    years: int,
    down_payment: float = 0.0
) -> Dict[str, float]:
    """
    Calculate monthly mortgage payment with amortization details.

    This tool computes the monthly payment for a fixed-rate mortgage,
    including principal, interest, total payment, and total interest.
    Use this when users ask about mortgage calculations, home loans,
    or monthly payment estimates.

    Args:
        loan_amount: Total loan amount in dollars (must be positive)
        annual_rate: Annual interest rate as percentage (e.g., 5.5 for 5.5%)
        years: Loan term in years (typically 15 or 30)
        down_payment: Down payment amount in dollars (default: 0)

    Returns:
        Dictionary containing monthly_payment, total_payment, total_interest,
        principal_amount, and effective_rate

    Examples:
        1. Input: {"loan_amount": 300000, "annual_rate": 6.5, "years": 30}
           → Output: {"monthly_payment": 1896.20, "total_payment": 682632, "total_interest": 382632}
        2. Input: {"loan_amount": 200000, "annual_rate": 5.0, "years": 15, "down_payment": 40000}
           → Output: {"monthly_payment": 1265.30, "total_payment": 227754, "total_interest": 67754}

    Raises:
        ValueError: If loan_amount or years are not positive
        ValidationError: If inputs are invalid
    """
    # Validate inputs
    loan_amount = ToolOutputValidator.validate_numeric(
        loan_amount,
        min_value=1000.0,
        max_value=100000000.0
    )
    annual_rate = ToolOutputValidator.validate_numeric(
        annual_rate,
        min_value=0.01,
        max_value=30.0
    )
    years = int(ToolOutputValidator.validate_numeric(
        years,
        min_value=1,
        max_value=50
    ))
    down_payment = ToolOutputValidator.validate_numeric(
        down_payment,
        min_value=0.0
    )

    # Calculate principal after down payment
    principal = loan_amount - down_payment

    if principal <= 0:
        raise ValueError("Loan amount must be greater than down payment")

    # Calculate monthly payment
    monthly_rate = (annual_rate / 100) / 12
    num_payments = years * 12

    if monthly_rate == 0:
        monthly_payment = principal / num_payments
    else:
        monthly_payment = principal * (
            monthly_rate * (1 + monthly_rate) ** num_payments
        ) / ((1 + monthly_rate) ** num_payments - 1)

    total_payment = monthly_payment * num_payments
    total_interest = total_payment - principal

    return {
        "monthly_payment": round(monthly_payment, 2),
        "total_payment": round(total_payment, 2),
        "total_interest": round(total_interest, 2),
        "principal_amount": principal,
        "loan_term_years": years,
        "annual_rate": annual_rate,
        "down_payment": down_payment,
    }


# Register with examples
tool_registry.register(
    calculate_mortgage_payment,
    examples=[
        {
            "input": {"loan_amount": 300000, "annual_rate": 6.5, "years": 30},
            "output": {"monthly_payment": 1896.20, "total_interest": 382632}
        }
    ]
)
```

## Testing Your Tools

Always write tests for your tools:

```python
import pytest
from app.tools.your_module import your_tool
from app.utils.validators import ValidationError

class TestYourTool:
    def test_basic_usage(self):
        """Test basic tool usage."""
        result = your_tool(arg1="value1", arg2="value2")

        assert "expected_key" in result
        assert result["expected_key"] > 0

    def test_invalid_input(self):
        """Test that invalid input raises error."""
        with pytest.raises(ValidationError):
            your_tool(arg1="invalid")

    def test_edge_cases(self):
        """Test edge cases."""
        # Test with minimum values
        result = your_tool(arg1=0.01)
        assert result is not None

        # Test with maximum values
        result = your_tool(arg1=999999)
        assert result is not None
```

## Available Validators

### Numeric Validation

```python
from app.utils.validators import ToolOutputValidator

value = ToolOutputValidator.validate_numeric(
    value=42.5,
    min_value=0.0,
    max_value=100.0
)
```

### String Validation

```python
city = ToolOutputValidator.validate_string(
    value="New York",
    min_length=2,
    max_length=100,
    pattern=r'^[A-Za-z\s]+$'  # Letters and spaces only
)
```

### Dictionary Validation

```python
data = ToolOutputValidator.validate_dict(
    value={"key1": "value1", "key2": "value2"},
    required_keys=["key1", "key2"]
)
```

### Date Validation

```python
date = ToolOutputValidator.validate_date(
    value="2024-01-15"  # String or datetime object
)
```

### Output Sanitization

```python
# Automatically sanitize output (removes scripts, limits length)
safe_output = ToolOutputValidator.sanitize_output(
    value=user_generated_content,
    max_length=10000
)
```

## Adding Tools to API

To make tools available in the API, register them in `app/api/routes.py`:

```python
# In app/api/routes.py
from app.tools import your_module

# Register your tool
tool_registry.register(
    your_module.your_tool,
    examples=[...]
)
```

## Common Patterns

### API Integration Tools

```python
import httpx

async def fetch_from_api(query: str) -> dict:
    """
    Fetch data from external API.

    Args:
        query: Search query

    Returns:
        API response data
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.example.com/search",
            params={"q": query}
        )
        response.raise_for_status()
        return response.json()
```

### Database Query Tools

```python
from typing import List, Dict

def query_database(table: str, filters: Dict[str, any]) -> List[Dict]:
    """
    Query database with filters.

    Args:
        table: Table name
        filters: Dictionary of column:value filters

    Returns:
        List of matching rows
    """
    # Your database query logic
    pass
```

### File Processing Tools

```python
def process_file(file_path: str, operation: str) -> dict:
    """
    Process a file with specified operation.

    Args:
        file_path: Path to file
        operation: Operation to perform ('read', 'analyze', 'convert')

    Returns:
        Processing result
    """
    # Your file processing logic
    pass
```

## Troubleshooting

### Tool Not Being Called

1. Check tool description is clear and relevant to query
2. Ensure examples are included in docstring
3. Verify tool is registered in the registry
4. Check LLM provider supports function calling

### Validation Errors

1. Ensure type hints match actual types
2. Use appropriate validators for input types
3. Handle edge cases (empty strings, None values, etc.)

### Schema Generation Issues

1. Verify function has proper docstring
2. Check parameter descriptions are in Args: section
3. Ensure type hints are present

## Advanced Topics

### Dynamic Tool Loading

```python
# Load tools from configuration
def load_tools_from_config(config_path: str):
    """Load and register tools from configuration file."""
    import importlib

    with open(config_path) as f:
        config = json.load(f)

    for tool_config in config["tools"]:
        module = importlib.import_module(tool_config["module"])
        func = getattr(module, tool_config["function"])
        tool_registry.register(func, examples=tool_config.get("examples"))
```

### Caching Tool Results

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def expensive_calculation(x: float, y: float) -> float:
    """Expensive calculation with caching."""
    # This result will be cached for repeated calls
    return complex_calculation(x, y)
```

### Async Tools

```python
async def async_tool(query: str) -> dict:
    """Asynchronous tool example."""
    # Note: Current implementation is synchronous
    # For async support, modify ToolAgent to use asyncio
    pass
```

## Summary Checklist

When creating a new tool, ensure:

- [ ] Function has comprehensive docstring
- [ ] Type hints are present for all parameters
- [ ] Args section in docstring describes each parameter
- [ ] Examples are included showing inputs and outputs
- [ ] Input validation is implemented
- [ ] Return value is a structured dictionary
- [ ] Tool is registered with the registry
- [ ] Unit tests are written
- [ ] Edge cases are handled
- [ ] Error messages are clear and helpful

---

For more information, see:
- [API Documentation](API.md)
- [Deployment Guide](DEPLOYMENT.md)
