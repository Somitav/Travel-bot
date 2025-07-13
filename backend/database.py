import logging
import os
import sys
from typing import Optional, Dict
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

# Add current directory to Python path for local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import ConversationState

logger = logging.getLogger("TravelBot")

# MongoDB configuration
MONGODB_URL = os.getenv("MONGODB_URL")
mongo_client: Optional[AsyncIOMotorClient] = None
database = None
conversations_collection = None

# In-memory fallback storage
in_memory_conversations: Dict[str, ConversationState] = {}
use_in_memory = False


async def init_database():
    """Initialize MongoDB connection and collections"""
    global mongo_client, database, conversations_collection, use_in_memory

    # If no MongoDB URL is provided, use in-memory storage
    if not MONGODB_URL:
        logger.warning("No MongoDB URL provided. Using in-memory storage for development.")
        use_in_memory = True
        return

    try:
        mongo_client = AsyncIOMotorClient(MONGODB_URL)
        database = mongo_client.get_database("travel-bot")
        conversations_collection = database.get_collection("conversations")

        # Test the connection
        await mongo_client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        logger.warning("Falling back to in-memory storage for development.")
        use_in_memory = True


async def close_database():
    """Close MongoDB connection"""
    global mongo_client
    if mongo_client:
        mongo_client.close()
        logger.info("MongoDB connection closed")


async def get_conversation_state(session_id: str) -> Optional[ConversationState]:
    """Retrieve conversation state from storage"""
    try:
        if use_in_memory:
            return in_memory_conversations.get(session_id)

        if conversations_collection is None:
            logger.error("Database not initialized")
            return None

        conversation_doc = await conversations_collection.find_one({"session_id": session_id})
        if conversation_doc:
            return ConversationState.from_dict(conversation_doc)
        return None
    except Exception as e:
        logger.error(f"Error retrieving conversation state: {e}")
        return None


async def save_conversation_state(state: ConversationState):
    """Save conversation state to storage"""
    try:
        state.updated_at = datetime.now()

        if use_in_memory:
            in_memory_conversations[state.session_id] = state
            return

        if conversations_collection is None:
            logger.error("Database not initialized")
            return

        await conversations_collection.replace_one(
            {"session_id": state.session_id},
            state.to_dict(),
            upsert=True
        )
    except Exception as e:
        logger.error(f"Error saving conversation state: {e}")


async def delete_conversation_state(session_id: str):
    """Delete conversation state from storage"""
    try:
        if use_in_memory:
            in_memory_conversations.pop(session_id, None)
            return

        if conversations_collection is None:
            logger.error("Database not initialized")
            return

        await conversations_collection.delete_one({"session_id": session_id})
    except Exception as e:
        logger.error(f"Error deleting conversation state: {e}")


async def get_all_conversations():
    """Get all conversations from storage (for admin purposes)"""
    try:
        if use_in_memory:
            return list(in_memory_conversations.values())

        if conversations_collection is None:
            logger.error("Database not initialized")
            return []

        conversations = []
        async for doc in conversations_collection.find():
            conversations.append(ConversationState.from_dict(doc))
        return conversations
    except Exception as e:
        logger.error(f"Error retrieving all conversations: {e}")
        return []
