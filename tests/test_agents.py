import pytest
from agents import PlannerAgent, ResearcherAgent, MemoryAgent, SynthesizerAgent

def test_planner_agent():
    """Test Planner Agent creation"""
    agent = PlannerAgent()
    assert agent is not None
    assert hasattr(agent, 'create_plan')

def test_researcher_agent():
    """Test Researcher Agent creation"""
    agent = ResearcherAgent()
    assert agent is not None
    assert hasattr(agent, 'conduct_research')

def test_memory_agent():
    """Test Memory Agent creation"""
    agent = MemoryAgent()
    assert agent is not None
    assert hasattr(agent, 'get_relevant_context')

def test_synthesizer_agent():
    """Test Synthesizer Agent creation"""
    agent = SynthesizerAgent()
    assert agent is not None
    assert hasattr(agent, 'synthesize_response')

@pytest.mark.skip(reason="Requires API key")
def test_planner_plan_creation():
    """Test plan creation (requires API key)"""
    agent = PlannerAgent()
    result = agent.create_plan("What is AI?")
    assert result['success'] == True
    assert 'plan' in result