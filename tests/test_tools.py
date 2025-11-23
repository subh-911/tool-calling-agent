"""
Unit tests for individual tools.
"""

import pytest
from datetime import datetime

from app.tools import financial, data, utilities
from app.utils.validators import ValidationError


class TestFinancialTools:
    """Tests for financial calculation tools."""

    def test_calculate_compound_interest_basic(self):
        """Test basic compound interest calculation."""
        result = financial.calculate_compound_interest(
            principal=1000.0,
            rate=5.0,
            years=10
        )

        assert "final_amount" in result
        assert "interest_earned" in result
        assert result["principal"] == 1000.0
        assert result["final_amount"] > 1000.0
        assert result["interest_earned"] > 0

    def test_calculate_compound_interest_with_compounding(self):
        """Test compound interest with quarterly compounding."""
        result = financial.calculate_compound_interest(
            principal=5000.0,
            rate=7.5,
            years=5,
            compounds_per_year=4
        )

        assert result["final_amount"] > 5000.0
        assert result["effective_rate"] > 7.5  # Should be higher with more frequent compounding

    def test_calculate_compound_interest_invalid_principal(self):
        """Test that negative principal raises error."""
        with pytest.raises(ValidationError):
            financial.calculate_compound_interest(
                principal=-1000.0,
                rate=5.0,
                years=10
            )

    def test_calculate_compound_interest_invalid_rate(self):
        """Test that invalid rate raises error."""
        with pytest.raises(ValidationError):
            financial.calculate_compound_interest(
                principal=1000.0,
                rate=150.0,  # Over 100%
                years=10
            )

    def test_convert_currency_basic(self):
        """Test basic currency conversion."""
        result = financial.convert_currency(
            amount=100.0,
            from_currency="USD",
            to_currency="EUR"
        )

        assert "converted_amount" in result
        assert "exchange_rate" in result
        assert result["from_currency"] == "USD"
        assert result["to_currency"] == "EUR"
        assert result["converted_amount"] > 0

    def test_convert_currency_same_currency(self):
        """Test conversion between same currency."""
        result = financial.convert_currency(
            amount=100.0,
            from_currency="USD",
            to_currency="USD"
        )

        assert result["converted_amount"] == 100.0
        assert result["exchange_rate"] == 1.0

    def test_convert_currency_invalid_currency(self):
        """Test that invalid currency code raises error."""
        with pytest.raises(ValueError):
            financial.convert_currency(
                amount=100.0,
                from_currency="XXX",  # Valid format but unsupported currency
                to_currency="USD"
            )

    def test_convert_currency_invalid_amount(self):
        """Test that negative amount raises error."""
        with pytest.raises(ValidationError):
            financial.convert_currency(
                amount=-100.0,
                from_currency="USD",
                to_currency="EUR"
            )


class TestDataTools:
    """Tests for data retrieval tools."""

    def test_get_weather_basic(self):
        """Test basic weather retrieval."""
        result = data.get_weather(city="New York")

        assert "temperature" in result
        assert "condition" in result
        assert "humidity" in result
        assert "wind_speed" in result
        assert result["city"] == "New York"

    def test_get_weather_celsius(self):
        """Test weather with celsius units."""
        result = data.get_weather(city="London", units="celsius")

        assert result["temperature_unit"] == "°C"
        assert result["wind_unit"] == "km/h"

    def test_get_weather_fahrenheit(self):
        """Test weather with fahrenheit units."""
        result = data.get_weather(city="New York", units="fahrenheit")

        assert result["temperature_unit"] == "°F"
        assert result["wind_unit"] == "mph"

    def test_get_weather_consistency(self):
        """Test that same city returns consistent results."""
        result1 = data.get_weather(city="Tokyo")
        result2 = data.get_weather(city="Tokyo")

        # Mock data should be deterministic per city
        assert result1["temperature"] == result2["temperature"]
        assert result1["condition"] == result2["condition"]

    def test_get_weather_invalid_units(self):
        """Test that invalid units raise error."""
        with pytest.raises(ValidationError):
            data.get_weather(city="Paris", units="kelvin")


class TestUtilityTools:
    """Tests for utility tools."""

    def test_calculate_date_difference_basic(self):
        """Test basic date difference calculation."""
        result = utilities.calculate_date_difference(
            start_date="2024-01-01",
            end_date="2024-12-31"
        )

        assert result["days"] == 365
        assert result["weeks"] == 52
        assert result["months"] == 11
        assert result["years"] == 1

    def test_calculate_date_difference_swapped(self):
        """Test that dates are swapped if start > end."""
        result = utilities.calculate_date_difference(
            start_date="2024-12-31",
            end_date="2024-01-01"
        )

        assert result["days"] == 365
        assert result["dates_swapped"] is True

    def test_calculate_date_difference_business_days(self):
        """Test business days calculation."""
        # One week = 5 business days
        result = utilities.calculate_date_difference(
            start_date="2024-01-01",  # Monday
            end_date="2024-01-08"     # Next Monday
        )

        assert result["business_days"] == 5

    def test_calculate_date_difference_invalid_format(self):
        """Test that invalid date format raises error."""
        with pytest.raises(ValueError):
            utilities.calculate_date_difference(
                start_date="01-01-2024",  # Wrong format
                end_date="2024-12-31"
            )

    def test_analyze_text_basic(self):
        """Test basic text analysis."""
        result = utilities.analyze_text("Hello world! This is a test.")

        assert result["word_count"] == 6
        assert result["sentence_count"] == 2
        assert result["character_count"] > 0
        assert result["unique_words"] <= result["word_count"]

    def test_analyze_text_empty_raises_error(self):
        """Test that empty text raises error."""
        with pytest.raises(ValidationError):
            utilities.analyze_text("")

    def test_analyze_text_readability(self):
        """Test readability score calculation."""
        simple_text = "The cat sat. The dog ran. Fun day."
        result = utilities.analyze_text(simple_text)

        assert "readability_score" in result
        assert "readability_level" in result
        assert 0 <= result["readability_score"] <= 100

    def test_analyze_text_sentiment(self):
        """Test sentiment analysis."""
        positive_text = "I love this! It's amazing and wonderful!"
        result = utilities.analyze_text(positive_text)

        assert result["sentiment"] == "positive"
        assert result["positive_word_count"] > 0

        negative_text = "This is terrible and awful. I hate it!"
        result = utilities.analyze_text(negative_text)

        assert result["sentiment"] == "negative"
        assert result["negative_word_count"] > 0

    def test_analyze_text_unique_words(self):
        """Test unique word counting."""
        result = utilities.analyze_text("test test test hello hello")

        assert result["word_count"] == 5
        assert result["unique_words"] == 2


class TestToolValidation:
    """Tests for tool output validation."""

    def test_tools_return_expected_types(self):
        """Test that all tools return dictionaries."""
        # Financial tools
        result = financial.calculate_compound_interest(1000, 5, 10)
        assert isinstance(result, dict)

        result = financial.convert_currency(100, "USD", "EUR")
        assert isinstance(result, dict)

        # Data tools
        result = data.get_weather("Tokyo")
        assert isinstance(result, dict)

        # Utility tools
        result = utilities.calculate_date_difference("2024-01-01", "2024-12-31")
        assert isinstance(result, dict)

        result = utilities.analyze_text("Test text")
        assert isinstance(result, dict)

    def test_tools_handle_edge_cases(self):
        """Test tools with edge case inputs."""
        # Very small values
        result = financial.calculate_compound_interest(0.01, 0.1, 1)
        assert result["final_amount"] > 0

        # Very long time periods
        result = financial.calculate_compound_interest(1000, 5, 100)
        assert result["final_amount"] > 1000

        # Single character text
        result = utilities.analyze_text("A")
        assert result["word_count"] == 1
