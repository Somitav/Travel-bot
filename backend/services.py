import logging
import json
import re
import asyncio
from typing import AsyncGenerator
from groq import Groq
from dotenv import load_dotenv

from models import ConversationState
from database import get_conversation_state, save_conversation_state
from utils import is_greeting, normalize_dates_in_text, clean_entity_value, get_missing_info_questions

load_dotenv()

logger = logging.getLogger("TravelBot")

# Initialize Groq client
client = Groq()

DEFAULT_DOMESTIC_COUNTRY = "India"


def extract_entities(user_input: str, state: ConversationState) -> ConversationState:
    """Extract travel entities from user input using AI"""
    logger.info("Extracting entities...")
    normalized_input = normalize_dates_in_text(user_input)

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
- For trip_duration, extract number of days as integer.
- For dates, use YYYY-MM-DD format.
"""

    try:
        response = client.chat.completions.create(
            model="deepseek-r1-distill-llama-70b",
            messages=[
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": normalized_input.strip()}
            ],
            temperature=0
        )

        raw_reply = response.choices[0].message.content
        if raw_reply is None:
            raw_reply = ""
        raw_reply = raw_reply.strip()

        match = re.search(r'\{.*\}', raw_reply, flags=re.DOTALL)
        if match:
            json_str = match.group(0)
            data = json.loads(json_str)

            # Only update fields that are not already set
            if not state.destination:
                state.destination = clean_entity_value(data.get("destination"))
            if not state.flying_from:
                state.flying_from = clean_entity_value(data.get("flying_from"))
            if not state.start_date:
                state.start_date = clean_entity_value(data.get("start_date"))
            if not state.end_date:
                state.end_date = clean_entity_value(data.get("end_date"))
            if not state.trip_duration:
                trip_duration = data.get("trip_duration")
                state.trip_duration = int(trip_duration) if isinstance(trip_duration, int) and trip_duration > 0 else None
            if not state.scope:
                state.scope = clean_entity_value(data.get("region_preference"))
            if not state.theme:
                state.theme = clean_entity_value(data.get("travel_type"))
        else:
            logger.warning("No valid JSON found in model response.")
    except Exception as e:
        logger.warning(f"Failed to extract entities: {e}")

    logger.info(f"Extracted: {state.to_dict()}")
    return state


async def generate_itinerary(state: ConversationState) -> str:
    """Generate travel itinerary using AI"""
    logger.info("Generating itinerary...")

    prompt = (
        f"Create a detailed travel itinerary for a trip from {state.flying_from or DEFAULT_DOMESTIC_COUNTRY} "
        f"to {state.destination} starting on {state.start_date} for {state.trip_duration} days. "
        f"Format the response as a well-structured itinerary with day-by-day activities, "
        f"including morning, afternoon, and evening activities. Make it engaging and practical."
    )

    if state.theme:
        prompt += f" Focus on {state.theme}-themed activities."

    try:
        response = client.chat.completions.create(
            model="deepseek-r1-distill-llama-70b",
            messages=[
                {"role": "system", "content": "You are a professional travel planner. Create detailed, practical itineraries."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        itinerary = response.choices[0].message.content
        if itinerary is None:
            itinerary = "I apologize, but I couldn't generate an itinerary at this time. Please try again."

        state.itinerary = itinerary
        logger.info("Itinerary generated successfully")
        return itinerary
    except Exception as e:
        logger.error(f"Error generating itinerary: {e}")
        return "I apologize, but I encountered an error while generating your itinerary. Please try again."


async def process_user_message(session_id: str, user_message: str) -> AsyncGenerator[str, None]:
    """Process user message and generate appropriate responses"""
    # Get or create conversation state
    state = await get_conversation_state(session_id)
    if not state:
        state = ConversationState(session_id)

    state.add_message("user", user_message)

    # Handle greeting
    if state.conversation_step == "greeting":
        if is_greeting(user_message):
            greeting_response = (
                "Hi there! I'm Travel Bot, your AI travel assistant. "
                "How can I help you plan your next adventure? "
                "You can tell me about your travel plans, like 'I want to plan a 3-day trip to Paris' "
                "or 'I'm looking for a romantic getaway for 5 days'."
            )
            state.add_message("bot", greeting_response)
            await save_conversation_state(state)
            yield f"data: {json.dumps({'type': 'message', 'content': greeting_response})}\n\n"
            return
        else:
            # User didn't greet, but provided travel info directly
            state.conversation_step = "gathering_info"
            greeting_response = (
                "Hello! I'm Travel Bot, your AI travel assistant. "
                "I see you're ready to plan a trip! Let me help you with that."
            )
            state.add_message("bot", greeting_response)
            await save_conversation_state(state)
            yield f"data: {json.dumps({'type': 'message', 'content': greeting_response})}\n\n"

            # Process the travel request
            await asyncio.sleep(0.5)  # Small delay for better UX

    # Extract entities from user message
    if state.conversation_step == "gathering_info" or state.conversation_step == "greeting":
        state.conversation_step = "gathering_info"
        extract_entities(user_message, state)

        # Check what information is still missing
        missing_fields = state.get_missing_fields()
        state.missing_fields = missing_fields

        if missing_fields:
            # Ask for missing information
            questions = get_missing_info_questions()

            next_question = questions.get(missing_fields[0])
            if next_question:
                response = f"Great! I have some information about your trip. {next_question}"
                state.add_message("bot", response)
                await save_conversation_state(state)
                yield f"data: {json.dumps({'type': 'message', 'content': response})}\n\n"
                return

        # All information collected, generate itinerary
        state.conversation_step = "generating_itinerary"
        confirmation_message = (
            f"Perfect! I have all the information I need:\n"
            f"• Destination: {state.destination}\n"
            f"• From: {state.flying_from}\n"
            f"• Start Date: {state.start_date}\n"
            f"• Duration: {state.trip_duration} days\n\n"
            f"Let me create a detailed itinerary for you..."
        )
        state.add_message("bot", confirmation_message)
        await save_conversation_state(state)
        yield f"data: {json.dumps({'type': 'message', 'content': confirmation_message})}\n\n"

        # Generate itinerary
        await asyncio.sleep(1)  # Show "thinking" delay
        itinerary = await generate_itinerary(state)
        state.conversation_step = "completed"

        itinerary_response = f"Here's your personalized {state.trip_duration}-day itinerary for {state.destination}:\n\n{itinerary}"
        state.add_message("bot", itinerary_response)
        await save_conversation_state(state)
        yield f"data: {json.dumps({'type': 'itinerary', 'content': itinerary_response})}\n\n"

        # Offer additional help
        follow_up = "Would you like me to adjust anything in your itinerary or help you plan another trip?"
        state.add_message("bot", follow_up)
        await save_conversation_state(state)
        yield f"data: {json.dumps({'type': 'message', 'content': follow_up})}\n\n"

    elif state.conversation_step == "completed":
        # Handle post-itinerary conversation
        if "another trip" in user_message.lower() or "new trip" in user_message.lower():
            # Reset state for new trip
            state.destination = None
            state.flying_from = None
            state.start_date = None
            state.end_date = None
            state.trip_duration = None
            state.itinerary = None
            state.theme = None
            state.scope = None
            state.conversation_step = "gathering_info"
            state.missing_fields = []

            response = "Great! I'd be happy to help you plan another trip. What kind of adventure are you thinking of next?"
            state.add_message("bot", response)
            await save_conversation_state(state)
            yield f"data: {json.dumps({'type': 'message', 'content': response})}\n\n"
        else:
            # General conversation or itinerary modifications
            response = (
                "I'm here to help with your travel planning! "
                "You can ask me to modify your itinerary, plan a new trip, or ask any travel-related questions."
            )
            state.add_message("bot", response)
            await save_conversation_state(state)
            yield f"data: {json.dumps({'type': 'message', 'content': response})}\n\n"
