import logging
import json
import os
from typing import Optional, Dict
from datetime import datetime
import re
from groq import Groq
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TravelBot")

# Setup Groq client
client = Groq(api_key=os.environ["GROQ_API_KEY"])

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
    greetings = ["hello", "hi", "hey", "good morning", "good evening", "good afternoon", "greetings"]
    text = text.lower()
    return any(greet in text for greet in greetings)

# Handle greeting
def handle_greeting():
    print("Hello! I'm your travel assistant. How can I help you plan your trip?")

# Extract entities using Groq model
def extract_entities(state: TravelState) -> TravelState:
    logger.info("Extracting entities...")

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

if __name__ == "__main__":
    main()
