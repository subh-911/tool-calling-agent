"""
Utility tools for date calculations and text analysis.

Best Practice: Rich descriptions with examples for better accuracy.
"""

from typing import Dict
from datetime import datetime, timedelta
import re
from app.utils.validators import ToolOutputValidator


def calculate_date_difference(
    start_date: str,
    end_date: str,
    format: str = "%Y-%m-%d"
) -> Dict[str, any]:
    """
    Calculate the difference between two dates.

    This tool computes the time difference between two dates, returning
    the duration in multiple units (days, weeks, months, years) and
    providing business day calculations.

    Args:
        start_date: Start date as string (e.g., '2024-01-01')
        end_date: End date as string (e.g., '2024-12-31')
        format: Date format string (default: '%Y-%m-%d' for YYYY-MM-DD)

    Returns:
        Dictionary with days, weeks, months, years, and business_days

    Supported formats:
        - '%Y-%m-%d': 2024-01-01 (YYYY-MM-DD)
        - '%Y-%m-%d %H:%M:%S': 2024-01-01 12:30:00
        - '%d/%m/%Y': 01/01/2024 (DD/MM/YYYY)
        - '%m/%d/%Y': 01/01/2024 (MM/DD/YYYY)

    Examples:
        1. Input: {"start_date": "2024-01-01", "end_date": "2024-12-31"} → Output: {"days": 365, "weeks": 52, "months": 12, "years": 1}
        2. Input: {"start_date": "2024-01-15", "end_date": "2024-02-15"} → Output: {"days": 31, "weeks": 4, "months": 1, "years": 0}
        3. Input: {"start_date": "2023-06-01", "end_date": "2024-06-01"} → Output: {"days": 366, "weeks": 52, "months": 12, "years": 1}
    """
    # Validate inputs
    start_date_str = ToolOutputValidator.validate_string(start_date, min_length=8, max_length=30)
    end_date_str = ToolOutputValidator.validate_string(end_date, min_length=8, max_length=30)

    # Parse dates
    try:
        start_dt = datetime.strptime(start_date_str, format)
        end_dt = datetime.strptime(end_date_str, format)
    except ValueError as e:
        raise ValueError(f"Invalid date format. Expected '{format}'. Error: {str(e)}")

    # Ensure start is before end
    if start_dt > end_dt:
        start_dt, end_dt = end_dt, start_dt
        dates_swapped = True
    else:
        dates_swapped = False

    # Calculate differences
    delta = end_dt - start_dt
    total_days = delta.days

    # Calculate business days (exclude weekends)
    business_days = 0
    current = start_dt
    while current < end_dt:
        if current.weekday() < 5:  # Monday = 0, Sunday = 6
            business_days += 1
        current += timedelta(days=1)

    # Calculate approximate months and years
    months = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month)
    years = total_days // 365

    return {
        "days": total_days,
        "weeks": total_days // 7,
        "months": months,
        "years": years,
        "business_days": business_days,
        "start_date": start_date_str,
        "end_date": end_date_str,
        "dates_swapped": dates_swapped,
    }


def analyze_text(text: str) -> Dict[str, any]:
    """
    Analyze text and return various statistics and insights.

    This tool performs comprehensive text analysis including word count,
    character count, sentence analysis, readability metrics, and
    basic sentiment indicators.

    Args:
        text: Text string to analyze (max 10,000 characters)

    Returns:
        Dictionary with word_count, character_count, sentence_count,
        average_word_length, unique_words, readability_score, and sentiment_indicators

    Examples:
        1. Input: {"text": "Hello world! This is a test."} → Output: {"word_count": 6, "sentence_count": 2, "avg_word_length": 4.5}
        2. Input: {"text": "Python is amazing. I love coding in Python!"} → Output: {"word_count": 8, "sentence_count": 2, "unique_words": 7}
        3. Input: {"text": "The quick brown fox jumps over the lazy dog."} → Output: {"word_count": 9, "sentence_count": 1, "avg_word_length": 3.9}
    """
    # Validate and sanitize input
    text = ToolOutputValidator.validate_string(text, min_length=1, max_length=10000)

    # Word analysis
    words = re.findall(r'\b\w+\b', text.lower())
    word_count = len(words)
    unique_words = len(set(words))

    # Character analysis
    char_count = len(text)
    char_count_no_spaces = len(text.replace(" ", ""))

    # Sentence analysis
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    sentence_count = len(sentences)

    # Average calculations
    avg_word_length = sum(len(word) for word in words) / word_count if word_count > 0 else 0
    avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0

    # Simple readability score (Flesch Reading Ease approximation)
    # Higher score = easier to read (0-100 scale)
    syllable_estimate = sum(max(1, len(re.findall(r'[aeiou]', word))) for word in words)
    avg_syllables_per_word = syllable_estimate / word_count if word_count > 0 else 0

    readability_score = 206.835 - 1.015 * avg_sentence_length - 84.6 * avg_syllables_per_word
    readability_score = max(0, min(100, readability_score))  # Clamp to 0-100

    # Basic sentiment indicators (simple keyword-based)
    positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'love', 'happy', 'best', 'fantastic', 'awesome']
    negative_words = ['bad', 'terrible', 'awful', 'hate', 'worst', 'horrible', 'sad', 'angry', 'poor', 'disappointing']

    positive_count = sum(1 for word in words if word in positive_words)
    negative_count = sum(1 for word in words if word in negative_words)

    if positive_count > negative_count:
        sentiment = "positive"
    elif negative_count > positive_count:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    return {
        "word_count": word_count,
        "unique_words": unique_words,
        "character_count": char_count,
        "character_count_no_spaces": char_count_no_spaces,
        "sentence_count": sentence_count,
        "average_word_length": round(avg_word_length, 2),
        "average_sentence_length": round(avg_sentence_length, 2),
        "readability_score": round(readability_score, 1),
        "readability_level": _get_readability_level(readability_score),
        "sentiment": sentiment,
        "positive_word_count": positive_count,
        "negative_word_count": negative_count,
    }


def _get_readability_level(score: float) -> str:
    """
    Convert readability score to human-readable level.

    Args:
        score: Readability score (0-100)

    Returns:
        Readability level description
    """
    if score >= 90:
        return "Very Easy (5th grade)"
    elif score >= 80:
        return "Easy (6th grade)"
    elif score >= 70:
        return "Fairly Easy (7th grade)"
    elif score >= 60:
        return "Standard (8th-9th grade)"
    elif score >= 50:
        return "Fairly Difficult (10th-12th grade)"
    elif score >= 30:
        return "Difficult (College)"
    else:
        return "Very Difficult (College graduate)"
