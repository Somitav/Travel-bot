import logging
import os
from typing import Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from models import ConversationState

logger = logging.getLogger("TravelBot")

# MongoDB configuration
MONGODB_URL = os.getenv("MONGODB_URL")
mongo_client: Optional[AsyncIOMotorClient] = None
database = None
conversations_collection = None


async def init_database():
    """Initialize MongoDB connection and collections"""
    global mongo_client, database, conversations_collection
    try:
        mongo_client = AsyncIOMotorClient(MONGODB_URL)
        database = mongo_client.get_database("travel-bot")
        conversations_collection = database.get_collection("conversations")

        # Test the connection
        await mongo_client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise e


async def close_database():
    """Close MongoDB connection"""
    global mongo_client
    if mongo_client:
        mongo_client.close()
        logger.info("MongoDB connection closed")


async def get_conversation_state(session_id: str) -> Optional[ConversationState]:
    """Retrieve conversation state from MongoDB"""
    try:
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
    """Save conversation state to MongoDB"""
    try:
        if conversations_collection is None:
            logger.error("Database not initialized")
            return

        state.updated_at = datetime.now()
        await conversations_collection.replace_one(
            {"session_id": state.session_id},
            state.to_dict(),
            upsert=True
        )
    except Exception as e:
        logger.error(f"Error saving conversation state: {e}")


async def delete_conversation_state(session_id: str):
    """Delete conversation state from MongoDB"""
    try:
        if conversations_collection is None:
            logger.error("Database not initialized")
            return

        await conversations_collection.delete_one({"session_id": session_id})
    except Exception as e:
        logger.error(f"Error deleting conversation state: {e}")


async def get_all_conversations():
    """Get all conversations from MongoDB (for admin purposes)"""
    try:
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
