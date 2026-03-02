from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from workflows import finder_workflow
from memory import conversation_memory
from database import snowflake_client, queries
from utils import logger, generate_session_id
from tools.amadeus_tool import verify_hotel_amadeus
import json
import re


router = APIRouter()


# ── REQUEST / RESPONSE MODELS ──

class HotelSearchRequest(BaseModel):
    location: str = Field(..., description="City or area to search")
    checkin: Optional[str] = Field(None, description="Check-in date (YYYY-MM-DD)")
    checkout: Optional[str] = Field(None, description="Check-out date (YYYY-MM-DD)")
    budget: Optional[str] = Field(None, description="Max price per night")
    guests: int = Field(2, description="Number of guests")
    preferences: Optional[str] = Field(None, description="Hotel preferences")
    session_id: Optional[str] = Field(None, description="Session identifier")


class HotelSearchResponse(BaseModel):
    response: str
    session_id: str
    hotels_found: int
    search_id: Optional[str] = None
    success: bool
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class HotelComparisonRequest(BaseModel):
    hotel_name: str
    location: str
    session_id: Optional[str] = None


class HotelVerifyRequest(BaseModel):
    hotel_id: str = Field(..., description="Amadeus Hotel ID e.g. BWPAR679")
    hotel_name: str = Field(..., description="Hotel name for display")
    checkin: str = Field(..., description="Check-in date YYYY-MM-DD")
    checkout: str = Field(..., description="Check-out date YYYY-MM-DD")
    original_price: float = Field(..., description="Price shown during initial search")
    adults: int = Field(2, description="Number of adults")
    session_id: Optional[str] = None


# ── ROUTES ──

@router.post("/hotels/search", response_model=HotelSearchResponse)
async def search_hotels(request: HotelSearchRequest, background_tasks: BackgroundTasks):
    """
    Search for hotels using the multi-agent AI system.
    """
    try:
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

        result = finder_workflow.execute(query=query, session_id=session_id)

        # Count bullet-point hotels in response
        hotels_found = len([
            line for line in result.get("response", "").split("\n")
            if line.strip().startswith("•")
        ])

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


@router.post("/hotels/verify")
async def verify_hotel(request: HotelVerifyRequest, background_tasks: BackgroundTasks):
    """
    Verify real-time availability and price for a specific hotel.
    Triggered when user clicks 'Check Live Price' on a hotel card.
    """
    try:
        logger.info(f"API: Verifying hotel {request.hotel_id} - {request.hotel_name}")

        result = verify_hotel_amadeus(
            hotel_id=request.hotel_id,
            check_in=request.checkin,
            check_out=request.checkout,
            adults=request.adults
        )

        # Calculate price change
        price_changed   = False
        price_direction = None
        price_diff      = 0.0

        if result["available"] and request.original_price:
            price_diff = round(result["current_price"] - request.original_price, 2)
            if abs(price_diff) > 0.5:
                price_changed   = True
                price_direction = "up" if price_diff > 0 else "down"

        # Save to Snowflake in background
        if result["available"]:
            background_tasks.add_task(
                save_verification_background,
                session_id=request.session_id or "unknown",
                hotel_id=request.hotel_id,
                hotel_name=request.hotel_name,
                original_price=request.original_price,
                current_price=result["current_price"],
                checkin=request.checkin,
                checkout=request.checkout
            )

        return {
            "available":       result["available"],
            "hotel_id":        request.hotel_id,
            "hotel_name":      request.hotel_name,
            "original_price":  request.original_price,
            "current_price":   result.get("current_price"),
            "price_changed":   price_changed,
            "price_direction": price_direction,
            "price_diff":      abs(price_diff),
            "offer_id":        result.get("offer_id"),
            "booking_link":    result.get("booking_link"),
            "message":         result.get("message"),
            "checked_at":      datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"API: Hotel verify failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hotels/compare")
async def compare_hotel(request: HotelComparisonRequest):
    """
    Compare prices for a specific hotel across platforms.
    """
    try:
        session_id = request.session_id or generate_session_id()
        query      = f"Compare prices for {request.hotel_name} in {request.location} across booking platforms"

        logger.info(f"API: Hotel comparison - {request.hotel_name}")

        result = finder_workflow.execute(query=query, session_id=session_id)

        return {
            "response":   result["response"],
            "session_id": session_id,
            "success":    result["success"]
        }

    except Exception as e:
        logger.error(f"API: Hotel comparison failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hotels/searches/{session_id}")
async def get_hotel_searches(session_id: str):
    """Get hotel search history for a session."""
    try:
        history = conversation_memory.get_history(session_id)
        hotel_messages = [
            msg for msg in history
            if "hotel" in msg.get("content", "").lower()
        ]
        return {
            "session_id": session_id,
            "searches":   hotel_messages,
            "count":      len(hotel_messages)
        }

    except Exception as e:
        logger.error(f"API: Failed to get hotel searches: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hotels/popular-destinations")
async def get_popular_destinations(days: int = 30, limit: int = 10):
    """Get most searched hotel destinations from Snowflake analytics."""
    try:
        return {
            "message": "Popular destinations analytics (requires Snowflake)",
            "note":    "Set up Snowflake to enable analytics"
        }
    except Exception as e:
        logger.error(f"API: Failed to get popular destinations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── BACKGROUND TASKS ──

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
    """Save hotel search to Snowflake (non-blocking)."""
    try:
        search_id     = generate_session_id()
        checkin_date  = checkin  if checkin  else None
        checkout_date = checkout if checkout else None

        budget_amount = None
        if budget:
            match = re.search(r'\d+', str(budget))
            if match:
                budget_amount = float(match.group())

        snowflake_client.execute_write(
            queries.INSERT_HOTEL_SEARCH,
            (
                search_id,
                session_id,
                session_id,
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


def save_verification_background(
    session_id: str,
    hotel_id: str,
    hotel_name: str,
    original_price: float,
    current_price: float,
    checkin: str,
    checkout: str
):
    """Save hotel verification/selection to Snowflake (non-blocking)."""
    try:
        logger.info(f"Background: Saving verification for {hotel_name} — ${current_price}/night")
        # TODO: add Snowflake query when HOTEL_VERIFICATIONS table is ready
        # snowflake_client.execute_write(queries.INSERT_HOTEL_VERIFICATION, (...))

    except Exception as e:
        logger.error(f"Background: Failed to save verification: {e}")