from typing import List, Dict
from memory.conversation_memory import conversation_memory
from utils import logger


class ContextManager:
    """
    Manages context window for LLM interactions.
    Formats conversation history for agent consumption.
    """
    
    def __init__(self):
        self.memory = conversation_memory
    
    def get_context_for_agent(self, session_id: str, include_last_n: int = 5) -> str:
        """
        Get formatted context for an agent
        
        Args:
            session_id: Session identifier
            include_last_n: Number of recent messages to include
            
        Returns:
            Formatted context string
        """
        history = self.memory.get_last_n_messages(session_id, include_last_n)
        
        if not history:
            return "No previous conversation history."
        
        # Format history
        formatted = "Previous conversation:\n\n"
        for msg in history:
            role = msg["role"].upper()
            content = msg["content"]
            formatted += f"{role}: {content}\n\n"
        
        return formatted.strip()
    
    def get_langchain_messages(self, session_id: str, include_last_n: int = 10) -> List[Dict]:
        """
        Get messages in LangChain format
        
        Args:
            session_id: Session identifier
            include_last_n: Number of recent messages to include
            
        Returns:
            List of messages in LangChain format
        """
        history = self.memory.get_last_n_messages(session_id, include_last_n)
        
        langchain_messages = []
        for msg in history:
            langchain_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        return langchain_messages
    
    def summarize_context(self, session_id: str) -> str:
        """
        Get a brief summary of the conversation
        
        Args:
            session_id: Session identifier
            
        Returns:
            Summary string
        """
        history = self.memory.get_history(session_id)
        
        if not history:
            return "No conversation history."
        
        user_messages = [msg for msg in history if msg["role"] == "user"]
        assistant_messages = [msg for msg in history if msg["role"] == "assistant"]
        
        summary = f"Session {session_id} - "
        summary += f"{len(user_messages)} user messages, "
        summary += f"{len(assistant_messages)} assistant responses"
        
        if user_messages:
            last_user_msg = user_messages[-1]["content"][:100]
            summary += f"\nLast query: {last_user_msg}..."
        
        return summary


# Global context manager instance
context_manager = ContextManager()