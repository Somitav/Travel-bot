import re
from datetime import datetime
import dateparser


def is_greeting(text: str) -> bool:
    """Check if the text is a greeting message"""
    greetings = ["hello", "hi", "hey", "good morning", "good evening", "good afternoon", "greetings", "hi there", "hello there"]
    text = text.lower().strip()

    # Check if it's a simple greeting (3 words or less and contains greeting words)
    if len(text.split()) <= 3 and any(greet in text for greet in greetings):
        return True

    # Check if it's exactly a greeting phrase
    return text in greetings


def normalize_dates_in_text(text: str) -> str:
    """Normalize date expressions in text to standard format"""
    patterns = [
        r"\btoday\b", r"\btomorrow\b", r"\byesterday\b",
        r"\bnext\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        r"\bthis\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        r"\b(?:on\s+)?\d{1,2}(st|nd|rd|th)?\s+(january|february|march|april|may|june|july|august|september|october|november|december)\b",
        r"\b(?:on\s+)?(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(st|nd|rd|th)?\b",
    ]

    # Handle "between X and Y" patterns
    between_pattern = r"between\s+(.*?)\s+and\s+(.*?)([\.!\?]|$)"
    match = re.search(between_pattern, text, flags=re.IGNORECASE)
    if match:
        date1 = dateparser.parse(match.group(1), settings={"RELATIVE_BASE": datetime.now()})
        date2 = dateparser.parse(match.group(2), settings={"RELATIVE_BASE": datetime.now()})
        if date1 and date2:
            text = text.replace(match.group(0), f"from {date1.strftime('%Y-%m-%d')} to {date2.strftime('%Y-%m-%d')}")

    # Handle individual date patterns
    for pattern in patterns:
        matches = re.finditer(pattern, text, flags=re.IGNORECASE)
        for match in matches:
            parsed_date = dateparser.parse(match.group(0), settings={"RELATIVE_BASE": datetime.now()})
            if parsed_date:
                text = text.replace(match.group(0), parsed_date.strftime("%Y-%m-%d"))

    return text


def clean_entity_value(val):
    """Clean and validate entity values from AI extraction"""
    return None if val in ["null", "", "None"] else val


def get_missing_info_questions():
    """Get questions for missing travel information"""
    return {
        "destination": "Where would you like to travel to?",
        "flying_from": "Which city or country are you traveling from?",
        "start_date": "When would you like to start your trip? (Please provide a date in YYYY-MM-DD format)",
        "trip_duration": "How many days would you like your trip to be?"
    }
