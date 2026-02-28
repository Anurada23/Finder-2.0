from typing import Dict, List, Optional
from datetime import datetime, timedelta
from config import settings
from utils import logger, format_message


class ConversationMemory:
    """
    Manages conversation history for sessions.
    Stores messages in memory with session-based isolation.
    """
    
    def __init__(self):
        self.sessions: Dict[str, List[Dict]] = {}
        self.session_timestamps: Dict[str, datetime] = {}
        self.max_history = settings.max_conversation_history
        
    def add_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        """
        Add a message to session history
        
        Args:
            session_id: Session identifier
            role: Message role (user/assistant/system)
            content: Message content
            metadata: Optional metadata
        """
        # Initialize session if doesn't exist
        if session_id not in self.sessions:
            self.sessions[session_id] = []
            logger.info(f"Created new session: {session_id}")
        
        # Create message
        message = format_message(role, content, metadata)
        
        # Add to session
        self.sessions[session_id].append(message)
        
        # Update timestamp
        self.session_timestamps[session_id] = datetime.utcnow()
        
        # Trim if exceeds max history
        if len(self.sessions[session_id]) > self.max_history:
            removed = self.sessions[session_id].pop(0)
            logger.debug(f"Trimmed message from session {session_id}: {removed['id']}")
        
        logger.debug(f"Added {role} message to session {session_id}")
    
    def get_history(self, session_id: str, limit: Optional[int] = None) -> List[Dict]:
        """
        Get conversation history for a session
        
        Args:
            session_id: Session identifier
            limit: Optional limit on number of messages
            
        Returns:
            List of messages
        """
        if session_id not in self.sessions:
            logger.warning(f"Session not found: {session_id}")
            return []
        
        history = self.sessions[session_id]
        
        if limit:
            history = history[-limit:]
        
        return history
    
    def get_last_n_messages(self, session_id: str, n: int = 5) -> List[Dict]:
        """Get the last N messages from a session"""
        return self.get_history(session_id, limit=n)
    
    def clear_session(self, session_id: str):
        """Clear a specific session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            del self.session_timestamps[session_id]
            logger.info(f"Cleared session: {session_id}")
    
    def cleanup_old_sessions(self):
        """Remove sessions older than timeout period"""
        timeout = timedelta(minutes=settings.session_timeout_minutes)
        current_time = datetime.utcnow()
        
        sessions_to_remove = [
            sid for sid, timestamp in self.session_timestamps.items()
            if current_time - timestamp > timeout
        ]
        
        for session_id in sessions_to_remove:
            self.clear_session(session_id)
            logger.info(f"Cleaned up expired session: {session_id}")
    
    def get_session_count(self) -> int:
        """Get number of active sessions"""
        return len(self.sessions)
    
    def session_exists(self, session_id: str) -> bool:
        """Check if session exists"""
        return session_id in self.sessions


# Global memory instance
conversation_memory = ConversationMemory()