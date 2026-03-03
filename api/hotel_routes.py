from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from workflows import finder_workflow
from memory import conversation_memory
from database import snowflake_client, queries
from utils import logger, generate_session_id
from tools.amadeus_tool import find_hotel_by_name, verify_hotel_amadeus
import httpx
import re


router = APIRouter()

N8N_WEBHOOK_URL = "http://localhost:5678/webhook/hotel-verify"


# ── MODELS ──

class HotelSearchRequest(BaseModel):
    location:    str            = Field(..., description="City or area to search")
    checkin:     Optional[str]  = Field(None, description="Check-in date YYYY-MM-DD")
    checkout:    Optional[str]  = Field(None, description="Check-out date YYYY-MM-DD")
    budget:      Optional[str]  = Field(None, description="Max price per night")
    guests:      int            = Field(2, description="Number of guests")
    preferences: Optional[str]  = Field(None, description="Hotel preferences")
    session_id:  Optional[str]  = Field(None, description="Session identifier")


class HotelSearchResponse(BaseModel):
    response:     str
    session_id:   str
    hotels_found: int
    search_id:    Optional[str] = None
    success:      bool
    timestamp:    str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class HotelComparisonRequest(BaseModel):
    hotel_name: str
    location:   str
    session_id: Optional[str] = None


class HotelVerifyRequest(BaseModel):
    hotel_name:     str   = Field(..., description="Hotel name from search results")
    city:           str   = Field(..., description="City name e.g. Paris")
    checkin:        str   = Field(..., description="Check-in date YYYY-MM-DD")
    checkout:       str   = Field(..., description="Check-out date YYYY-MM-DD")
    original_price: float = Field(..., description="Price shown during search")
    adults:         int   = Field(2, description="Number of adults")
    session_id:     Optional[str] = None


class HotelVerifyDirectRequest(BaseModel):
    hotel_name:     str   = Field(..., description="Hotel name for fuzzy matching")
    city:           str   = Field(..., description="City name")
    checkin:        str   = Field(..., description="Check-in date YYYY-MM-DD")
    checkout:       str   = Field(..., description="Check-out date YYYY-MM-DD")
    original_price: float = Field(..., description="Original price for comparison")
    adults:         int   = Field(2)
    session_id:     Optional[str] = None


# ── ROUTES ──

@router.post("/hotels/search", response_model=HotelSearchResponse)
async def search_hotels(request: HotelSearchRequest, background_tasks: BackgroundTasks):
    """Search hotels using multi-agent AI pipeline."""
    try:
        session_id = request.session_id or generate_session_id()

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
    Triggered by frontend 'Check Live Price' button.
    Forwards to n8n webhook — n8n handles Amadeus verification.
    Falls back to verify-direct if n8n unreachable.
    """
    try:
        logger.info(f"API: Verify request for '{request.hotel_name}' in {request.city} → n8n")

        # ── Try n8n first ──
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                n8n_res = await client.post(
                    N8N_WEBHOOK_URL,
                    json={
                        "hotel_name":     request.hotel_name,
                        "city":           request.city,
                        "checkin":        request.checkin,
                        "checkout":       request.checkout,
                        "original_price": request.original_price,
                        "adults":         request.adults,
                        "session_id":     request.session_id or "unknown"
                    }
                )

            if n8n_res.status_code == 200:
                data = n8n_res.json()
                logger.info(f"API: n8n verify success for '{request.hotel_name}'")
                return {
                    "available":       data.get("available", False),
                    "hotel_name":      request.hotel_name,
                    "matched_name":    data.get("matched_name", request.hotel_name),
                    "original_price":  request.original_price,
                    "current_price":   data.get("current_price"),
                    "price_changed":   data.get("price_status") != "unchanged",
                    "price_direction": "down" if data.get("price_status") == "decreased"
                                       else "up" if data.get("price_status") == "increased"
                                       else None,
                    "price_diff":      data.get("price_diff", 0),
                    "booking_link":    f"https://www.booking.com/search.html?ss={request.hotel_name}",
                    "message":         "Verified via n8n",
                    "checked_at":      data.get("checked_at", datetime.utcnow().isoformat()),
                    "source":          "n8n"
                }

        except httpx.ConnectError:
            logger.warning("API: n8n not reachable — falling back to verify-direct")
        except Exception as n8n_err:
            logger.warning(f"API: n8n error — falling back: {n8n_err}")

        # ── Fallback: call verify-direct logic directly ──
        return await _run_verify_direct(
            hotel_name=request.hotel_name,
            city=request.city,
            checkin=request.checkin,
            checkout=request.checkout,
            original_price=request.original_price,
            adults=request.adults,
            session_id=request.session_id,
            background_tasks=background_tasks,
            source="direct"
        )

    except Exception as e:
        logger.error(f"API: Hotel verify failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hotels/verify-direct")
async def verify_hotel_direct(request: HotelVerifyDirectRequest, background_tasks: BackgroundTasks):
    """
    Called by n8n only — NOT by frontend directly.
    Runs full Amadeus chain: name → IATA → Hotel ID → live price.
    """
    try:
        logger.info(f"API: verify-direct for '{request.hotel_name}' in {request.city}")
        return await _run_verify_direct(
            hotel_name=request.hotel_name,
            city=request.city,
            checkin=request.checkin,
            checkout=request.checkout,
            original_price=request.original_price,
            adults=request.adults,
            session_id=request.session_id,
            background_tasks=background_tasks,
            source="n8n"
        )

    except Exception as e:
        logger.error(f"API: verify-direct failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _run_verify_direct(
    hotel_name: str,
    city: str,
    checkin: str,
    checkout: str,
    original_price: float,
    adults: int,
    session_id: Optional[str],
    background_tasks: BackgroundTasks,
    source: str = "direct"
) -> dict:
    """
    Shared logic for verify-direct and fallback.
    Step 1: name → Hotel ID via find_hotel_by_name
    Step 2: Hotel ID → live price via verify_hotel_amadeus
    """

    # Step 1 — find Hotel ID by name
    match = find_hotel_by_name(hotel_name=hotel_name, city=city)

    if not match.get("found") or not match.get("hotel_id"):
        return {
            "available":      False,
            "hotel_name":     hotel_name,
            "original_price": original_price,
            "current_price":  None,
            "price_changed":  False,
            "price_direction": None,
            "price_diff":     0,
            "message":        match.get("message", "Hotel not found in Amadeus"),
            "checked_at":     datetime.utcnow().isoformat(),
            "source":         source
        }

    hotel_id     = match["hotel_id"]
    matched_name = match["matched_name"]

    # Step 2 — verify live price
    result = verify_hotel_amadeus(
        hotel_id=hotel_id,
        check_in=checkin,
        check_out=checkout,
        adults=adults
    )

    # Price change detection
    price_changed   = False
    price_direction = None
    price_diff      = 0.0

    if result["available"] and original_price:
        price_diff = round(result["current_price"] - original_price, 2)
        if abs(price_diff) > 0.5:
            price_changed   = True
            price_direction = "up" if price_diff > 0 else "down"

    # Save to Snowflake in background
    if result["available"]:
        background_tasks.add_task(
            save_verification_background,
            session_id=session_id or "unknown",
            hotel_id=hotel_id,
            hotel_name=matched_name,
            original_price=original_price,
            current_price=result["current_price"],
            checkin=checkin,
            checkout=checkout
        )

    return {
        "available":       result["available"],
        "hotel_id":        hotel_id,
        "hotel_name":      hotel_name,
        "matched_name":    matched_name,
        "original_price":  original_price,
        "current_price":   result.get("current_price"),
        "price_changed":   price_changed,
        "price_direction": price_direction,
        "price_diff":      abs(price_diff),
        "offer_id":        result.get("offer_id"),
        "booking_link":    f"https://www.booking.com/search.html?ss={hotel_name}",
        "message":         result.get("message"),
        "checked_at":      datetime.utcnow().isoformat(),
        "source":          source
    }


@router.post("/hotels/compare")
async def compare_hotel(request: HotelComparisonRequest):
    """Compare prices for a specific hotel."""
    try:
        session_id = request.session_id or generate_session_id()
        query      = f"Compare prices for {request.hotel_name} in {request.location}"
        result     = finder_workflow.execute(query=query, session_id=session_id)
        return {"response": result["response"], "session_id": session_id, "success": result["success"]}
    except Exception as e:
        logger.error(f"API: Hotel comparison failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hotels/searches/{session_id}")
async def get_hotel_searches(session_id: str):
    """Get hotel search history for a session."""
    try:
        history = conversation_memory.get_history(session_id)
        hotel_messages = [msg for msg in history if "hotel" in msg.get("content", "").lower()]
        return {"session_id": session_id, "searches": hotel_messages, "count": len(hotel_messages)}
    except Exception as e:
        logger.error(f"API: Failed to get hotel searches: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hotels/popular-destinations")
async def get_popular_destinations(days: int = 30, limit: int = 10):
    try:
        return {"message": "Popular destinations analytics (requires Snowflake)"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── BACKGROUND TASKS ──

def save_hotel_search_background(
    session_id: str, location: str, checkin: Optional[str],
    checkout: Optional[str], budget: Optional[str], guests: int,
    preferences: Optional[str], response: str
):
    try:
        search_id     = generate_session_id()
        budget_amount = None
        if budget:
            match = re.search(r'\d+', str(budget))
            if match:
                budget_amount = float(match.group())

        snowflake_client.execute_write(
            queries.INSERT_HOTEL_SEARCH,
            (search_id, session_id, session_id, location,
             checkin, checkout, guests, budget_amount, preferences or "")
        )
        logger.info(f"Background: Saved hotel search {search_id}")
    except Exception as e:
        logger.error(f"Background: Failed to save hotel search: {e}")


def save_verification_background(
    session_id: str, hotel_id: str, hotel_name: str,
    original_price: float, current_price: float,
    checkin: str, checkout: str
):
    try:
        logger.info(f"Background: Saving verification for {hotel_name} — ${current_price}/night")
        # TODO: add Snowflake query when HOTEL_VERIFICATIONS table is ready
    except Exception as e:
        logger.error(f"Background: Failed to save verification: {e}")