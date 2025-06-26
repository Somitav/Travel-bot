import logging
import json
import os
from typing import Optional, Dict
from datetime import datetime
import re
from groq import Groq
from dotenv import load_dotenv
import dateparser

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TravelBot")

client = Groq()

DEFAULT_DOMESTIC_COUNTRY = "India"

class TravelState:
    def __init__(self, user_input: str):
        self.user_input = user_input
        self.destination: Optional[str] = None
        self.flying_from: Optional[str] = None
        self.start_date: Optional[str] = None
        self.end_date: Optional[str] = None
        self.trip_duration: Optional[int] = None
        self.itinerary: Optional[str] = None
        self.theme: Optional[str] = None
        self.scope: Optional[str] = None  # 'domestic' or 'international'

    def to_dict(self) -> Dict:
        return {
            "destination": self.destination,
            "flying_from": self.flying_from,
            "start_date": self.start_date,
            "trip_duration": self.trip_duration,
            "theme": self.theme,
            "scope": self.scope
        }

def is_greeting(text: str) -> bool:
    greetings = ["hello", "hi", "hey", "good morning", "good evening", "good afternoon", "greetings", "hi there", "hello there"]
    text = text.lower().strip()
    return text in greetings or (len(text.split()) <= 3 and any(greet in text for greet in greetings))

def handle_greeting():
    print("Hello! I'm your travel assistant. How can I help you plan your trip?")

def normalize_dates_in_text(text: str) -> str:
    patterns = [
        r"\btoday\b", r"\btomorrow\b", r"\byesterday\b",
        r"\bnext\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        r"\bthis\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        r"\b(?:on\s+)?\d{1,2}(st|nd|rd|th)?\s+(january|february|march|april|may|june|july|august|september|october|november|december)\b",
        r"\b(?:on\s+)?(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(st|nd|rd|th)?\b",
    ]
    between_pattern = r"between\s+(.*?)\s+and\s+(.*?)([\.!\?]|$)"
    match = re.search(between_pattern, text, flags=re.IGNORECASE)
    if match:
        date1 = dateparser.parse(match.group(1), settings={"RELATIVE_BASE": datetime.now()})
        date2 = dateparser.parse(match.group(2), settings={"RELATIVE_BASE": datetime.now()})
        if date1 and date2:
            text = text.replace(match.group(0), f"from {date1.strftime('%Y-%m-%d')} to {date2.strftime('%Y-%m-%d')}")
    for pattern in patterns:
        matches = re.finditer(pattern, text, flags=re.IGNORECASE)
        for match in matches:
            parsed_date = dateparser.parse(match.group(0), settings={"RELATIVE_BASE": datetime.now()})
            if parsed_date:
                text = text.replace(match.group(0), parsed_date.strftime("%Y-%m-%d"))
    return text

def suggest_destinations_from_theme(state: TravelState) -> Optional[str]:
    themes = {
        "beach": {"domestic": ["Goa", "Varkala", "Pondicherry"], "international": ["Maldives", "Bali", "Phuket"]},
        "hill station": {"domestic": ["Manali", "Ooty", "Darjeeling"], "international": ["Swiss Alps", "Banff", "Nagano"]},
        "romantic": {"domestic": ["Udaipur", "Coorg"], "international": ["Paris", "Venice", "Santorini"]},
        "adventure": {"domestic": ["Rishikesh", "Leh"], "international": ["Queenstown", "Costa Rica"]},
        "food": {"domestic": ["Delhi", "Lucknow", "Kolkata"], "international": ["Bangkok", "Rome", "Tokyo"]},
        "wellness": {"domestic": ["Rishikesh", "Kerala"], "international": ["Bali", "Thailand"]}
    }

    detected = None
    for theme in themes:
        if theme in state.user_input.lower():
            detected = theme
            state.theme = theme
            break

    if not detected:
        return None

    if not state.scope:
        user_lower = state.user_input.lower()
        if any(keyword in user_lower for keyword in ["my country", "same country", "domestic"]):
            state.scope = "domestic"
            print(f"Assuming you want to travel within your country. Setting domestic country as {DEFAULT_DOMESTIC_COUNTRY}.")
            print("If you'd like to change this, please specify the country in your input.")
        elif "international" in user_lower:
            state.scope = "international"

    scope = state.scope or "international"
    suggestions = themes[detected][scope]

    print(f"I found you might be interested in a {detected.title()} trip. Here are some {scope} suggestions:")
    for i, place in enumerate(suggestions, 1):
        print(f"{i}. {place}")

    choice = input("Please select one of the above destinations (enter number or name): ").strip()
    if choice.isdigit():
        idx = int(choice)
        if 1 <= idx <= len(suggestions):
            return suggestions[idx - 1]
    elif choice in suggestions:
        return choice
    return None

def extract_entities(state: TravelState) -> TravelState:
    logger.info("Extracting entities...")
    state.user_input = normalize_dates_in_text(state.user_input)

    system_prompt = """
You are an AI travel assistant. Extract the following fields from the user's message and return only a JSON object:

{
  "destination": "...",
  "flying_from": "...",
  "start_date": "...",
  "end_date": "...",
  "trip_duration": ...,
  "travel_type": "...",
  "region_preference": "domestic" or "international" or null
}

- If any value is missing or cannot be clearly determined, use null.
- Only reply with the JSON object, without explanation or extra formatting.
"""

    response = client.chat.completions.create(
        model="deepseek-r1-distill-llama-70b",
        messages=[
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": state.user_input.strip()}
        ],
        temperature=0
    )

    raw_reply = response.choices[0].message.content.strip()

    try:
        match = re.search(r'\{.*\}', raw_reply, flags=re.DOTALL)
        if match:
            json_str = match.group(0)
            data = json.loads(json_str)
            def clean(val): return None if val in ["null", "", "None"] else val
            state.destination = clean(data.get("destination"))
            state.flying_from = clean(data.get("flying_from"))
            state.start_date = clean(data.get("start_date"))
            state.end_date = clean(data.get("end_date"))
            trip_duration = data.get("trip_duration")
            state.trip_duration = int(trip_duration) if isinstance(trip_duration, int) and trip_duration > 0 else None
            state.scope = clean(data.get("region_preference"))
            state.theme = clean(data.get("travel_type"))
        else:
            logger.warning("No valid JSON found in model response.")
    except Exception as e:
        logger.warning(f"Failed to parse JSON: {e}")

    logger.info(f"Extracted: {state.to_dict()}")
    return state

def fill_missing_info(state: TravelState) -> TravelState:
    if not state.destination:
        suggested = suggest_destinations_from_theme(state)
        if suggested:
            state.destination = suggested
        else:
            state.destination = input("Where do you want to travel to? ")

    if not state.flying_from:
        state.flying_from = input("Where are you flying from? ")

    while not state.start_date:
        s = input("When does your trip start? (YYYY-MM-DD): ")
        try:
            dt = datetime.strptime(s, "%Y-%m-%d").date()
            if dt < datetime.now().date():
                print("Start date can't be in the past.")
            else:
                state.start_date = s
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD.")

    if state.start_date and state.end_date and not state.trip_duration:
        try:
            start = datetime.strptime(state.start_date, "%Y-%m-%d")
            end = datetime.strptime(state.end_date, "%Y-%m-%d")
            diff = (end - start).days
            if diff > 0:
                state.trip_duration = diff
        except Exception as e:
            logger.warning(f"Could not calculate duration: {e}")

    while not state.trip_duration:
        try:
            dur = int(input("How many days is your trip? "))
            if dur <= 0:
                print("Trip duration must be greater than 0.")
            else:
                state.trip_duration = dur
        except ValueError:
            print("Please enter a valid number.")

    return state

def create_itinerary(state: TravelState) -> TravelState:
    logger.info("Generating itinerary...")

    prompt = (
        f"Create a detailed travel itinerary for a trip from {state.flying_from or DEFAULT_DOMESTIC_COUNTRY} "
        f"to {state.destination} starting on {state.start_date} for {state.trip_duration} days."
    )

    response = client.chat.completions.create(
        model="deepseek-r1-distill-llama-70b",
        messages=[
            {"role": "system", "content": "You are a professional travel planner."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    state.itinerary = response.choices[0].message.content
    logger.info("Itinerary generated.")
    return state

def main():
    print("Welcome to the Travel Bot!")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        if is_greeting(user_input):
            handle_greeting()
            continue

        state = TravelState(user_input)

        # Handle domestic assumption early
        if any(keyword in user_input.lower() for keyword in ["my country", "same country", "domestic"]):
            state.scope = "domestic"
            print(f"Assuming you want to travel within your country. Setting domestic country as {DEFAULT_DOMESTIC_COUNTRY}.")
            print("If you'd like to change this, please specify the country in your input.")

        state = extract_entities(state)

        # Reconfirm scope after extraction if still missing
        if not state.scope and any(keyword in user_input.lower() for keyword in ["my country", "same country", "domestic"]):
            state.scope = "domestic"

        state = fill_missing_info(state)
        state = create_itinerary(state)
        print("\nHere is your itinerary:\n")
        print(state.itinerary)
        print("\n")

if __name__ == "__main__":
    main()
