import logging
import json
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from database import init_database, close_database, get_conversation_state, delete_conversation_state
from services import process_user_message

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TravelBot")

# Initialize FastAPI app
app = FastAPI(title="Travel Bot API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("TravelBot API is running on port 8000")


# Application lifecycle events
@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    await init_database()


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    await close_database()


# API Routes
@app.get("/")
def read_root():
    """Root endpoint for health check"""
    return {"status": "Travel Bot API is running", "version": "1.0.0"}


@app.post("/chat/{session_id}")
async def chat_endpoint(session_id: str, request: Request):
    """
    Main chat endpoint that handles conversation with Server-Side Events

    Args:
        session_id: Unique identifier for the conversation session
        request: FastAPI request object containing the user message

    Returns:
        StreamingResponse: Server-Side Events stream with bot responses
    """
    try:
        body = await request.json()
        user_message = body.get("message", "").strip()

        if not user_message:
            return {"error": "Message is required"}

        async def event_generator():
            """Generate Server-Side Events for real-time communication"""
            async for chunk in process_user_message(session_id, user_message):
                yield chunk

            # Send session state update at the end
            state = await get_conversation_state(session_id)
            if state:
                yield f"data: {json.dumps({'type': 'state_update', 'state': state.to_dict()})}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return {"error": "An error occurred while processing your message"}


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """
    Get conversation session data

    Args:
        session_id: Unique identifier for the conversation session

    Returns:
        dict: Session data including state and messages
    """
    state = await get_conversation_state(session_id)
    if state:
        return {
            "session_id": session_id,
            "state": state.to_dict(),
            "messages": state.messages
        }
    return {"error": "Session not found"}


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a conversation session

    Args:
        session_id: Unique identifier for the conversation session

    Returns:
        dict: Confirmation message
    """
    await delete_conversation_state(session_id)
    return {"message": "Session deleted successfully"}


@app.get("/health")
def health_check():
    """
    Health check endpoint

    Returns:
        dict: Health status and timestamp
    """
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# Application entry point
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
