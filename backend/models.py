from typing import Optional, Dict, List
from datetime import datetime


class ConversationState:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.destination: Optional[str] = None
        self.flying_from: Optional[str] = None
        self.start_date: Optional[str] = None
        self.end_date: Optional[str] = None
        self.trip_duration: Optional[int] = None
        self.itinerary: Optional[str] = None
        self.theme: Optional[str] = None
        self.scope: Optional[str] = None  # 'domestic' or 'international'
        self.conversation_step = "greeting"  # greeting, gathering_info, generating_itinerary, completed
        self.messages: List[Dict] = []
        self.missing_fields: List[str] = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "destination": self.destination,
            "flying_from": self.flying_from,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "trip_duration": self.trip_duration,
            "theme": self.theme,
            "scope": self.scope,
            "conversation_step": self.conversation_step,
            "missing_fields": self.missing_fields,
            "messages": self.messages,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ConversationState":
        state = cls(data["session_id"])
        state.destination = data.get("destination")
        state.flying_from = data.get("flying_from")
        state.start_date = data.get("start_date")
        state.end_date = data.get("end_date")
        state.trip_duration = data.get("trip_duration")
        state.theme = data.get("theme")
        state.scope = data.get("scope")
        state.conversation_step = data.get("conversation_step", "greeting")
        state.messages = data.get("messages", [])
        state.missing_fields = data.get("missing_fields", [])
        created_at_str = data.get("created_at")
        state.created_at = datetime.fromisoformat(created_at_str) if created_at_str else datetime.now()
        updated_at_str = data.get("updated_at")
        state.updated_at = datetime.fromisoformat(updated_at_str) if updated_at_str else datetime.now()
        return state

    def add_message(self, role: str, content: str):
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.updated_at = datetime.now()

    def get_missing_fields(self) -> List[str]:
        missing = []
        if not self.destination:
            missing.append("destination")
        if not self.flying_from:
            missing.append("flying_from")
        if not self.start_date:
            missing.append("start_date")
        if not self.trip_duration:
            missing.append("trip_duration")
        return missing
