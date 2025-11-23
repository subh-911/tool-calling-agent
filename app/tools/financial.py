"""
Financial calculation tools.

Best Practice: Rich descriptions with examples for better accuracy.
"""

from typing import Dict
from app.utils.validators import ToolOutputValidator


def calculate_compound_interest(
    principal: float,
    rate: float,
    years: int,
    compounds_per_year: int = 1
) -> Dict[str, float]:
    """
    Calculate compound interest on an investment.

    This tool computes the future value of an investment with compound interest,
    showing the total amount, interest earned, and effective annual rate.

    Args:
        principal: Initial investment amount in dollars (must be positive)
        rate: Annual interest rate as a percentage (e.g., 5.5 for 5.5%)
        years: Number of years to compound (must be positive integer)
        compounds_per_year: Number of times interest is compounded per year (default: 1 for annual)

    Returns:
        Dictionary containing final_amount, interest_earned, and effective_rate

    Examples:
        1. Input: {"principal": 1000, "rate": 5, "years": 10} → Output: {"final_amount": 1628.89, "interest_earned": 628.89, "effective_rate": 5.0}
        2. Input: {"principal": 5000, "rate": 7.5, "years": 5, "compounds_per_year": 12} → Output: {"final_amount": 7229.31, "interest_earned": 2229.31, "effective_rate": 7.76}
        3. Input: {"principal": 10000, "rate": 3.25, "years": 20, "compounds_per_year": 4} → Output: {"final_amount": 18948.90, "interest_earned": 8948.90, "effective_rate": 3.29}

    Raises:
        ValueError: If principal or years are not positive
    """
    # Validate inputs
    principal = ToolOutputValidator.validate_numeric(principal, min_value=0.01)
    rate = ToolOutputValidator.validate_numeric(rate, min_value=0.0, max_value=100.0)
    years = int(ToolOutputValidator.validate_numeric(years, min_value=1))
    compounds_per_year = int(ToolOutputValidator.validate_numeric(compounds_per_year, min_value=1))

    # Calculate compound interest: A = P(1 + r/n)^(nt)
    rate_decimal = rate / 100
    final_amount = principal * (1 + rate_decimal / compounds_per_year) ** (compounds_per_year * years)
    interest_earned = final_amount - principal

    # Calculate effective annual rate
    effective_rate = ((1 + rate_decimal / compounds_per_year) ** compounds_per_year - 1) * 100

    return {
        "final_amount": round(final_amount, 2),
        "interest_earned": round(interest_earned, 2),
        "effective_rate": round(effective_rate, 2),
        "principal": principal,
        "years": years,
        "annual_rate": rate,
    }


def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str
) -> Dict[str, any]:
    """
    Convert amount between different currencies using current exchange rates.

    This tool converts money between major world currencies. In production,
    this would connect to a real-time exchange rate API. Currently uses
    mock rates for demonstration.

    Args:
        amount: Amount to convert (must be positive)
        from_currency: Source currency code (e.g., 'USD', 'EUR', 'GBP')
        to_currency: Target currency code (e.g., 'USD', 'EUR', 'GBP')

    Returns:
        Dictionary with converted_amount, exchange_rate, and timestamp

    Supported currencies: USD, EUR, GBP, JPY, CAD, AUD, CHF, CNY, INR

    Examples:
        1. Input: {"amount": 100, "from_currency": "USD", "to_currency": "EUR"} → Output: {"converted_amount": 92.50, "exchange_rate": 0.925}
        2. Input: {"amount": 1000, "from_currency": "GBP", "to_currency": "JPY"} → Output: {"converted_amount": 187500, "exchange_rate": 187.5}
        3. Input: {"amount": 50, "from_currency": "EUR", "to_currency": "USD"} → Output: {"converted_amount": 54.05, "exchange_rate": 1.081}

    Note:
        Exchange rates are mock values for demonstration. In production,
        integrate with services like exchangerate-api.com or fixer.io
    """
    # Validate inputs
    amount = ToolOutputValidator.validate_numeric(amount, min_value=0.01)
    from_currency = ToolOutputValidator.validate_string(from_currency, min_length=3, max_length=3, pattern=r'^[A-Z]{3}$')
    to_currency = ToolOutputValidator.validate_string(to_currency, min_length=3, max_length=3, pattern=r'^[A-Z]{3}$')

    # Mock exchange rates (relative to USD)
    # In production, fetch from API like exchangerate-api.com
    exchange_rates = {
        "USD": 1.0,
        "EUR": 0.925,
        "GBP": 0.805,
        "JPY": 150.0,
        "CAD": 1.35,
        "AUD": 1.52,
        "CHF": 0.88,
        "CNY": 7.24,
        "INR": 83.0,
    }

    # Validate supported currencies
    supported = list(exchange_rates.keys())
    if from_currency not in supported:
        raise ValueError(f"Unsupported currency: {from_currency}. Supported: {', '.join(supported)}")
    if to_currency not in supported:
        raise ValueError(f"Unsupported currency: {to_currency}. Supported: {', '.join(supported)}")

    # Convert to USD first, then to target currency
    usd_amount = amount / exchange_rates[from_currency]
    converted_amount = usd_amount * exchange_rates[to_currency]
    exchange_rate = exchange_rates[to_currency] / exchange_rates[from_currency]

    return {
        "converted_amount": round(converted_amount, 2),
        "exchange_rate": round(exchange_rate, 4),
        "from_currency": from_currency,
        "to_currency": to_currency,
        "original_amount": amount,
        "note": "Using mock exchange rates for demonstration",
    }
