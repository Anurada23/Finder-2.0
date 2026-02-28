from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
import operator


class WorkflowState(TypedDict):
    """
    State object that flows through the workflow graph.
    Each agent can read from and write to this state.
    """
    # Input
    query: str
    session_id: str
    
    # Context
    context: str
    has_history: bool
    
    # Plan
    research_plan: str
    
    # Research
    research_findings: str
    sources_used: list[str]
    
    # Output
    final_response: str
    
    # Metadata
    agent_outputs: dict
    error: str
    success: bool
    
    # Messages (for LangGraph)
    messages: Annotated[Sequence[BaseMessage], operator.add]