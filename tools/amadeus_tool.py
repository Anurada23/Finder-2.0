from config import settings
from utils import logger
import requests


def _get_amadeus_token() -> str:
    """Get Amadeus OAuth token"""
    res = requests.post(
        "https://test.api.amadeus.com/v1/security/oauth2/token",
        data={
            "grant_type":    "client_credentials",
            "client_id":     settings.amadeus_api_key,
            "client_secret": settings.amadeus_api_secret
        },
        timeout=10
    )
    res.raise_for_status()
    return res.json()["access_token"]


def _get_iata_code(city: str, token: str) -> str:
    """Convert city name to IATA code"""
    res = requests.get(
        "https://test.api.amadeus.com/v1/reference-data/locations/cities",
        headers={"Authorization": f"Bearer {token}"},
        params={"keyword": city, "max": 1},
        timeout=10
    )
    res.raise_for_status()
    data = res.json().get("data", [])
    if not data:
        raise ValueError(f"City '{city}' not found in Amadeus")
    return data[0]["iataCode"]


def _get_hotel_ids(city_code: str, token: str) -> list:
    """Get hotel IDs for a city"""
    res = requests.get(
        "https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-city",
        headers={"Authorization": f"Bearer {token}"},
        params={"cityCode": city_code, "ratings": "4,5"},
        timeout=10
    )
    res.raise_for_status()
    return [h["hotelId"] for h in res.json().get("data", [])[:50]]


def find_hotel_by_name(hotel_name: str, city: str) -> dict:
    """
    Find Amadeus Hotel ID by matching hotel name against city hotel list.
    Called by /verify-direct endpoint which n8n triggers.

    Args:
        hotel_name: Hotel name from web search e.g. "Le Meurice"
        city: City name e.g. "Paris"

    Returns:
        dict with hotel_id and matched_name
    """
    try:
        logger.info(f"Amadeus name lookup: '{hotel_name}' in {city}")

        token    = _get_amadeus_token()
        iata     = _get_iata_code(city, token)
        hotel_ids = _get_hotel_ids(iata, token)

        if not hotel_ids:
            return {"found": False, "hotel_id": None, "message": f"No hotels found in {city}"}

        # Get hotel names from Amadeus to fuzzy match against
        offers_res = requests.get(
            "https://test.api.amadeus.com/v3/shopping/hotel-offers",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "hotelIds": ",".join(hotel_ids[:20]),  # check first 20
                "currency": "USD",
                "bestRateOnly": True
            },
            timeout=15
        )
        offers_res.raise_for_status()
        offers = offers_res.json().get("data", [])

        if not offers:
            return {"found": False, "hotel_id": None, "message": "No offers returned"}

        # Fuzzy match — find closest hotel name
        hotel_name_lower = hotel_name.lower().strip()
        best_match       = None
        best_score       = 0

        for offer in offers:
            amadeus_name  = offer["hotel"]["name"].lower().strip()
            amadeus_id    = offer["hotel"]["hotelId"]

            # Simple word overlap scoring
            query_words   = set(hotel_name_lower.split())
            amadeus_words = set(amadeus_name.split())
            overlap       = len(query_words & amadeus_words)
            score         = overlap / max(len(query_words), 1)

            if score > best_score:
                best_score  = score
                best_match  = {
                    "hotel_id":     amadeus_id,
                    "matched_name": offer["hotel"]["name"],
                    "score":        score
                }

        if best_match and best_match["score"] > 0.3:
            logger.info(f"Matched '{hotel_name}' → '{best_match['matched_name']}' (score: {best_match['score']:.2f})")
            return {"found": True, **best_match}

        # No good match — use first available hotel as fallback
        logger.warning(f"No strong match for '{hotel_name}' — using first result")
        return {
            "found":        True,
            "hotel_id":     offers[0]["hotel"]["hotelId"],
            "matched_name": offers[0]["hotel"]["name"],
            "score":        0
        }

    except Exception as e:
        logger.error(f"find_hotel_by_name failed: {e}")
        return {"found": False, "hotel_id": None, "message": str(e)}


def verify_hotel_amadeus(hotel_id: str, check_in: str, check_out: str, adults: int = 2) -> dict:
    """
    Verify real-time availability and price for ONE specific hotel by ID.

    Args:
        hotel_id:  Amadeus Hotel ID e.g. BWPAR679
        check_in:  YYYY-MM-DD
        check_out: YYYY-MM-DD
        adults:    number of adults

    Returns:
        dict with availability, current_price, offer_id
    """
    try:
        logger.info(f"Amadeus verify: {hotel_id}, {check_in} to {check_out}")

        token = _get_amadeus_token()

        res = requests.get(
            "https://test.api.amadeus.com/v3/shopping/hotel-offers",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "hotelIds":     hotel_id,
                "checkInDate":  check_in,
                "checkOutDate": check_out,
                "adults":       adults,
                "currency":     "USD",
                "bestRateOnly": True
            },
            timeout=15
        )
        res.raise_for_status()
        data = res.json().get("data", [])

        if not data:
            return {
                "available": False,
                "hotel_id":  hotel_id,
                "message":   "No availability for these dates"
            }

        offer      = data[0]
        hotel      = offer["hotel"]
        price_info = offer["offers"][0]["price"]
        offer_id   = offer["offers"][0]["id"]

        return {
            "available":    True,
            "hotel_id":     hotel_id,
            "hotel_name":   hotel.get("name", ""),
            "current_price": float(price_info["total"]),
            "currency":     price_info.get("currency", "USD"),
            "offer_id":     offer_id,
            "check_in":     check_in,
            "check_out":    check_out,
            "message":      "Available"
        }

    except requests.exceptions.HTTPError as e:
        logger.error(f"Amadeus verify HTTP error: {e}")
        return {"available": False, "hotel_id": hotel_id, "message": str(e)}
    except Exception as e:
        logger.error(f"Amadeus verify failed: {e}")
        return {"available": False, "hotel_id": hotel_id, "message": str(e)}