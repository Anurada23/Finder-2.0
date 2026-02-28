import pytest
from tools import search_web, visit_website, retrieve_memory
from memory import conversation_memory

def test_search_tool_exists():
    """Test search tool is available"""
    assert search_web is not None
    assert callable(search_web)

def test_visit_website_tool_exists():
    """Test visit_website tool is available"""
    assert visit_website is not None
    assert callable(visit_website)

def test_memory_tool_exists():
    """Test memory tool is available"""
    assert retrieve_memory is not None
    assert callable(retrieve_memory)

@pytest.mark.skip(reason="Requires network")
def test_search_execution():
    """Test search execution (requires network)"""
    result = search_web.invoke("Python programming")
    assert result is not None
    assert len(result) > 0

def test_memory_with_session():
    """Test memory storage and retrieval"""
    session_id = "test-session-123"
    
    # Add test message
    conversation_memory.add_message(session_id, "user", "Hello")
    conversation_memory.add_message(session_id, "assistant", "Hi there!")
    
    # Retrieve history
    history = conversation_memory.get_history(session_id)
    
    assert len(history) == 2
    assert history[0]['role'] == 'user'
    assert history[1]['role'] == 'assistant'
    
    # Cleanup
    conversation_memory.clear_session(session_id)