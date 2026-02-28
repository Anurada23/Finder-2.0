from fastapi import APIRouter, HTTPException, BackgroundTasks
from api.schemas import (
    ResearchRequest, 
    ResearchResponse, 
    HealthResponse,
    ConversationHistoryResponse,
    WebhookRequest,
    WebhookResponse
)
from workflows import finder_workflow
from memory import conversation_memory
from database import snowflake_client, queries
from utils import logger, generate_session_id
import json


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="healthy")


@router.post("/research", response_model=ResearchResponse)
async def research(request: ResearchRequest, background_tasks: BackgroundTasks):
    """
    Main research endpoint.
    Executes the full agent workflow.
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or generate_session_id()
        
        logger.info(f"API: Research request - Session: {session_id}, Query: {request.query[:50]}...")
        
        # Execute workflow
        result = finder_workflow.execute(
            query=request.query,
            session_id=session_id
        )
        
        # Save to Snowflake in background
        background_tasks.add_task(
            save_to_snowflake_background,
            session_id=session_id,
            query=request.query,
            response=result.get("response", ""),
            plan=result.get("plan", ""),
            sources=result.get("sources", [])
        )
        
        return ResearchResponse(
            response=result["response"],
            session_id=session_id,
            plan=result.get("plan"),
            sources=result.get("sources", []),
            success=result["success"],
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"API: Research endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook", response_model=WebhookResponse)
async def n8n_webhook(request: WebhookRequest, background_tasks: BackgroundTasks):
    """
    n8n webhook endpoint.
    Receives requests from n8n workflows.
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or generate_session_id()
        
        logger.info(f"API: n8n webhook - Session: {session_id}")
        
        # Execute workflow
        result = finder_workflow.execute(
            query=request.query,
            session_id=session_id
        )
        
        # Save to Snowflake in background
        background_tasks.add_task(
            save_to_snowflake_background,
            session_id=session_id,
            query=request.query,
            response=result.get("response", ""),
            plan=result.get("plan", ""),
            sources=result.get("sources", [])
        )
        
        return WebhookResponse(
            response=result["response"],
            session_id=session_id,
            plan=result.get("plan"),
            sources=result.get("sources", []),
            success=result["success"],
            metadata=request.metadata
        )
        
    except Exception as e:
        logger.error(f"API: Webhook endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{session_id}", response_model=ConversationHistoryResponse)
async def get_history(session_id: str):
    """Get conversation history for a session"""
    try:
        history = conversation_memory.get_history(session_id)
        
        return ConversationHistoryResponse(
            session_id=session_id,
            messages=history,
            count=len(history)
        )
        
    except Exception as e:
        logger.error(f"API: Failed to get history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/{session_id}")
async def clear_history(session_id: str):
    """Clear conversation history for a session"""
    try:
        conversation_memory.clear_session(session_id)
        return {"message": f"Session {session_id} cleared successfully"}
        
    except Exception as e:
        logger.error(f"API: Failed to clear history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def save_to_snowflake_background(
    session_id: str,
    query: str,
    response: str,
    plan: str,
    sources: list
):
    """Background task to save data to Snowflake"""
    try:
        sources_str = json.dumps(sources)
        
        snowflake_client.execute_write(
            queries.INSERT_RESEARCH_SESSION,
            (session_id, query, response, plan, sources_str, 0, 0.0)
        )
        
        logger.info(f"Background: Saved session {session_id} to Snowflake")
        
    except Exception as e:
        logger.error(f"Background: Failed to save to Snowflake: {e}")