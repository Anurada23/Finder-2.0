from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from workflows import finder_workflow
from memory import conversation_memory
from database import snowflake_client, queries
from utils import logger, generate_session_id
import json


router = APIRouter()


class HotelSearchRequest(BaseModel):
    """Request model for hotel search"""
    location: str = Field(..., description="City or area to search")
    checkin: Optional[str] = Field(None, description="Check-in date (YYYY-MM-DD)")
    checkout: Optional[str] = Field(None, description="Check-out date (YYYY-MM-DD)")
    budget: Optional[str] = Field(None, description="Max price per night")
    guests: int = Field(2, description="Number of guests")
    preferences: Optional[str] = Field(None, description="Hotel preferences")
    session_id: Optional[str] = Field(None, description="Session identifier")


class HotelSearchResponse(BaseModel):
    """Response model for hotel search"""
    response: str
    session_id: str
    hotels_found: int
    search_id: Optional[str] = None
    success: bool
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class HotelComparisonRequest(BaseModel):
    """Request for price comparison"""
    hotel_name: str
    location: str
    session_id: Optional[str] = None


@router.post("/hotels/search", response_model=HotelSearchResponse)
async def search_hotels(request: HotelSearchRequest, background_tasks: BackgroundTasks):
    """
    Search for hotels based on criteria.
    Uses the multi-agent system to find and compare hotels.
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or generate_session_id()
        
        # Build natural language query
        query_parts = [f"Find hotels in {request.location}"]
        
        if request.checkin and request.checkout:
            query_parts.append(f"from {request.checkin} to {request.checkout}")
        
        if request.budget:
            query_parts.append(f"under {request.budget} per night")
        
        if request.guests > 2:
            query_parts.append(f"for {request.guests} guests")
        
        if request.preferences:
            query_parts.append(f"with {request.preferences}")
        
        query = " ".join(query_parts)
        
        logger.info(f"API: Hotel search - Session: {session_id}, Query: {query}")
        
        # Execute workflow
        result = finder_workflow.execute(
            query=query,
            session_id=session_id
        )
        
        # Extract number of hotels found (simple count)
        hotels_found = len([line for line in result.get("response", "").split("\n") if line.strip().startswith("•")])
        
        # Save to Snowflake in background
        background_tasks.add_task(
            save_hotel_search_background,
            session_id=session_id,
            location=request.location,
            checkin=request.checkin,
            checkout=request.checkout,
            budget=request.budget,
            guests=request.guests,
            preferences=request.preferences,
            response=result.get("response", "")
        )
        
        return HotelSearchResponse(
            response=result["response"],
            session_id=session_id,
            hotels_found=hotels_found,
            success=result["success"]
        )
        
    except Exception as e:
        logger.error(f"API: Hotel search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hotels/compare")
async def compare_hotel(request: HotelComparisonRequest):
    """
    Compare prices for a specific hotel across platforms.
    """
    try:
        session_id = request.session_id or generate_session_id()
        
        query = f"Compare prices for {request.hotel_name} in {request.location} across booking platforms"
        
        logger.info(f"API: Hotel comparison - {request.hotel_name}")
        
        result = finder_workflow.execute(
            query=query,
            session_id=session_id
        )
        
        return {
            "response": result["response"],
            "session_id": session_id,
            "success": result["success"]
        }
        
    except Exception as e:
        logger.error(f"API: Hotel comparison failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hotels/searches/{session_id}")
async def get_hotel_searches(session_id: str):
    """Get hotel search history for a session"""
    try:
        # This would query Snowflake for past searches
        # For now, return conversation history
        history = conversation_memory.get_history(session_id)
        
        # Filter for hotel-related messages
        hotel_messages = [
            msg for msg in history 
            if "hotel" in msg.get("content", "").lower()
        ]
        
        return {
            "session_id": session_id,
            "searches": hotel_messages,
            "count": len(hotel_messages)
        }
        
    except Exception as e:
        logger.error(f"API: Failed to get hotel searches: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hotels/popular-destinations")
async def get_popular_destinations(days: int = 30, limit: int = 10):
    """Get most searched hotel destinations"""
    try:
        # This would query Snowflake analytics
        # For now, return placeholder
        return {
            "message": "Popular destinations analytics (requires Snowflake)",
            "note": "Set up Snowflake to enable analytics"
        }
        
    except Exception as e:
        logger.error(f"API: Failed to get popular destinations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def save_hotel_search_background(
    session_id: str,
    location: str,
    checkin: Optional[str],
    checkout: Optional[str],
    budget: Optional[str],
    guests: int,
    preferences: Optional[str],
    response: str
):
    """Background task to save hotel search to Snowflake"""
    try:
        search_id = generate_session_id()
        
        # Parse dates if provided
        checkin_date = checkin if checkin else None
        checkout_date = checkout if checkout else None
        
        # Parse budget
        budget_amount = None
        if budget:
            import re
            match = re.search(r'\d+', str(budget))
            if match:
                budget_amount = float(match.group())
        
        snowflake_client.execute_write(
            queries.INSERT_HOTEL_SEARCH,
            (
                search_id,
                session_id,
                session_id,  # Using session as user_id for now
                location,
                checkin_date,
                checkout_date,
                guests,
                budget_amount,
                preferences or ""
            )
        )
        
        logger.info(f"Background: Saved hotel search {search_id} to Snowflake")
        
    except Exception as e:
        logger.error(f"Background: Failed to save hotel search: {e}")