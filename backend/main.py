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
# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TravelBot")

# Setup Groq client

print('api=', os.getenv("GROQ_API_KEY"))
client = Groq()







# Define shared state as simple dictionary
class TravelState:
    def __init__(self, user_input: str):
        self.user_input = user_input
        self.destination: Optional[str] = None
        self.flying_from: Optional[str] = None
        self.start_date: Optional[str] = None
        self.end_date: Optional[str] = None
        self.trip_duration: Optional[int] = None
        self.itinerary: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "destination": self.destination,
            "flying_from": self.flying_from,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "trip_duration": self.trip_duration,
        }

# Simple greeting detection
def is_greeting(text: str) -> bool:
    greetings = [
        "hello", "hi", "hey", "good morning", "good evening",
        "good afternoon", "greetings", "hi there", "hello there"
    ]
    text = text.lower().strip()
    return text in greetings or (len(text.split()) <= 3 and any(greet in text for greet in greetings))



# Handle greeting
def handle_greeting():
    print("Hello! I'm your travel assistant. How can I help you plan your trip?")

def normalize_dates_in_text(text: str) -> str:
    patterns = [
        r"\btoday\b",
        r"\btomorrow\b",
        r"\byesterday\b",
        r"\bnext\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        r"\bthis\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        r"\b(?:on\s+)?\d{1,2}(st|nd|rd|th)?\s+(january|february|march|april|may|june|july|august|september|october|november|december)\b",
        r"\b(?:on\s+)?(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(st|nd|rd|th)?\b",
    ]

    # Handle "between June 1st and June 10th"
    between_pattern = r"between\s+(.*?)\s+and\s+(.*?)([\.!\?]|$)"
    match = re.search(between_pattern, text, flags=re.IGNORECASE)
    if match:
        date1 = dateparser.parse(match.group(1), settings={"RELATIVE_BASE": datetime.now()})
        date2 = dateparser.parse(match.group(2), settings={"RELATIVE_BASE": datetime.now()})
        if date1 and date2:
            formatted1 = date1.strftime("%Y-%m-%d")
            formatted2 = date2.strftime("%Y-%m-%d")
            # Replace original range phrase
            full_match = match.group(0)
            text = text.replace(full_match, f"from {formatted1} to {formatted2}")

    # Replace all other patterns
    for pattern in patterns:
        matches = re.finditer(pattern, text, flags=re.IGNORECASE)
        for match in matches:
            full_match = match.group(0)
            parsed_date = dateparser.parse(full_match, settings={"RELATIVE_BASE": datetime.now()})
            if parsed_date:
                formatted = parsed_date.strftime("%Y-%m-%d")
                text = text.replace(full_match, formatted)

    return text

# Extract entities using Groq model
def extract_entities(state: TravelState) -> TravelState:
    logger.info("Extracting entities...")

    # Preprocess user input to replace relative dates with actual ones
    state.user_input = normalize_dates_in_text(state.user_input)

    system_prompt = """
You are an AI travel assistant. Extract entities from user's message and reply only in JSON format:
{
  "destination": "...",
  "flying_from": "...",
  "start_date": "...",
  "end_date": "...",
  "trip_duration": ...
}
If any field is missing, use null.
"""

    response = client.chat.completions.create(
        model="deepseek-r1-distill-llama-70b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": state.user_input}
        ],
        temperature=0
    )

    reply = response.choices[0].message.content

    try:
        data = json.loads(reply)
        state.destination = data.get("destination")
        state.flying_from = data.get("flying_from")
        state.start_date = data.get("start_date")
        state.end_date = data.get("end_date")
        state.trip_duration = data.get("trip_duration")
    except json.JSONDecodeError:
        logger.warning("Could not parse model output.")
        pass

    logger.info(f"Extracted: {state.to_dict()}")
    return state



# Ask user for missing fields
def fill_missing_info(state: TravelState) -> TravelState:
    if not state.destination:
        state.destination = input("Where do you want to travel to? ")
    if not state.flying_from:
        state.flying_from = input("Where are you flying from? ")
    if not state.start_date:
        state.start_date = input("When does your trip start? (YYYY-MM-DD) ")
    if not state.end_date and not state.trip_duration:
        choice = input("Do you want to specify end date or trip duration? (date/duration): ").lower()
        if choice == 'date':
            state.end_date = input("When does your trip end? (YYYY-MM-DD) ")
        else:
            state.trip_duration = int(input("How many days is your trip? "))
    return state


def validate_dates(start: Optional[str], end: Optional[str]) -> bool:
    today = datetime.now().date()
    try:
        if start:
            start_date = datetime.strptime(start, "%Y-%m-%d").date()
            if start_date < today:
                return False
        if end:
            end_date = datetime.strptime(end, "%Y-%m-%d").date()
            if end_date < today:
                return False
        if start and end:
            return start_date < end_date
        return True
    except Exception as e:
        logger.warning(f"Date validation failed: {e}")
        return False


# Generate itinerary
def create_itinerary(state: TravelState) -> TravelState:
    logger.info("Generating itinerary...")

    prompt = (
        f"Create a detailed travel itinerary for a trip from {state.flying_from} to {state.destination} "
        f"starting on {state.start_date} "
    )
    if state.end_date:
        prompt += f"and ending on {state.end_date}."
    else:
        prompt += f"for {state.trip_duration} days."

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

# Main conversation loop
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
        state = extract_entities(state)
        state = fill_missing_info(state)
        state = create_itinerary(state)

        print("\nHere is your itinerary:\n")
        print(state.itinerary)
        print("\n")

# Main conversation loop
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
        state = extract_entities(state)
        state = fill_missing_info(state)

        if not validate_dates(state.start_date, state.end_date):
            print(" Date is invalid or in the past. Please try again with future dates.")
            continue

        state = create_itinerary(state)

        print("\nHere is your itinerary:\n")
        print(state.itinerary)
        print("\n")

if __name__ == "__main__":
    main()



