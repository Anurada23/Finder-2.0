from langgraph.graph import StateGraph, END
from agents import PlannerAgent, ResearcherAgent, MemoryAgent, SynthesizerAgent
from workflows.state import WorkflowState
from utils import logger
from typing import Dict, Any


class FinderWorkflow:
    """
    Orchestrates the multi-agent workflow using LangGraph.
    Flow: Memory → Planner → Researcher → Synthesizer
    """
    
    def __init__(self):
        # Initialize agents
        self.memory_agent = MemoryAgent()
        self.planner_agent = PlannerAgent()
        self.researcher_agent = ResearcherAgent()
        self.synthesizer_agent = SynthesizerAgent()
        
        # Build graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the workflow graph"""
        
        # Create graph with state
        workflow = StateGraph(WorkflowState)
        
        # Add nodes (agents)
        workflow.add_node("memory", self._memory_node)
        workflow.add_node("planner", self._planner_node)
        workflow.add_node("researcher", self._researcher_node)
        workflow.add_node("synthesizer", self._synthesizer_node)
        
        # Define edges (flow)
        workflow.set_entry_point("memory")
        workflow.add_edge("memory", "planner")
        workflow.add_edge("planner", "researcher")
        workflow.add_edge("researcher", "synthesizer")
        workflow.add_edge("synthesizer", END)
        
        # Compile graph
        return workflow.compile()
    
    def _memory_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Memory agent node"""
        logger.info("Workflow: Executing Memory Agent")
        
        result = self.memory_agent(
            session_id=state["session_id"],
            current_query=state["query"]
        )
        
        return {
            "context": result.get("context", ""),
            "has_history": result.get("has_history", False),
            "agent_outputs": {
                **state.get("agent_outputs", {}),
                "memory": result
            }
        }
    
    def _planner_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Planner agent node"""
        logger.info("Workflow: Executing Planner Agent")
        
        result = self.planner_agent(
            query=state["query"],
            context=state.get("context", "")
        )
        
        return {
            "research_plan": result.get("plan", ""),
            "agent_outputs": {
                **state.get("agent_outputs", {}),
                "planner": result
            }
        }
    
    def _researcher_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Researcher agent node"""
        logger.info("Workflow: Executing Researcher Agent")
        
        result = self.researcher_agent(
            plan=state["research_plan"],
            query=state["query"]
        )
        
        # Extract sources from tool calls
        sources = []
        for tool_call in result.get("tool_calls", []):
            if "url" in str(tool_call):
                sources.append(str(tool_call))
        
        return {
            "research_findings": result.get("findings", ""),
            "sources_used": sources,
            "agent_outputs": {
                **state.get("agent_outputs", {}),
                "researcher": result
            }
        }
    
    def _synthesizer_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Synthesizer agent node"""
        logger.info("Workflow: Executing Synthesizer Agent")
        
        result = self.synthesizer_agent(
            query=state["query"],
            research_findings=state["research_findings"],
            context=state.get("context", ""),
            plan=state.get("research_plan", "")
        )
        
        return {
            "final_response": result.get("response", ""),
            "success": result.get("success", False),
            "agent_outputs": {
                **state.get("agent_outputs", {}),
                "synthesizer": result
            }
        }
    
    def execute(self, query: str, session_id: str) -> Dict[str, Any]:
        """
        Execute the complete workflow
        
        Args:
            query: User's query
            session_id: Session identifier
            
        Returns:
            Dictionary with final response and metadata
        """
        try:
            logger.info(f"Workflow: Starting execution for query: {query[:50]}...")
            
            # Initialize state
            initial_state = {
                "query": query,
                "session_id": session_id,
                "context": "",
                "has_history": False,
                "research_plan": "",
                "research_findings": "",
                "sources_used": [],
                "final_response": "",
                "agent_outputs": {},
                "error": "",
                "success": False,
                "messages": []
            }
            
            # Execute graph
            final_state = self.graph.invoke(initial_state)
            
            # Save to memory
            self.memory_agent.save_interaction(
                session_id=session_id,
                user_query=query,
                agent_response=final_state["final_response"]
            )
            
            logger.info("Workflow: Execution completed successfully")
            
            return {
                "response": final_state["final_response"],
                "plan": final_state.get("research_plan", ""),
                "sources": final_state.get("sources_used", []),
                "success": True,
                "agent_outputs": final_state.get("agent_outputs", {})
            }
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {
                "response": f"An error occurred: {str(e)}",
                "plan": "",
                "sources": [],
                "success": False,
                "error": str(e)
            }


# Global workflow instance
finder_workflow = FinderWorkflow()