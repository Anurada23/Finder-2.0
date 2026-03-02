from langchain_core.tools import tool
from config import settings
from utils import logger
import requests


def _get_amadeus_token() -> str:
    res = requests.post(
        "https://test.api.amadeus.com/v1/security/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": settings.amadeus_api_key,
            "client_secret": settings.amadeus_api_secret
        },
        timeout=10
    )
    res.raise_for_status()
    return res.json()["access_token"]


@tool
def search_hotels_amadeus(city: str, check_in: str, check_out: str, budget: float, adults: int = 1) -> str:
    """
    Search real hotel availability and prices using Amadeus API.
    Returns top 5 hotels with live pricing.
    """
    try:
        logger.info(f"Amadeus hotel search: {city}, {check_in} to {check_out}, budget ${budget}")

        token = _get_amadeus_token()
        headers = {"Authorization": f"Bearer {token}"}

        city_res = requests.get(
            "https://test.api.amadeus.com/v1/reference-data/locations/cities",
            headers=headers,
            params={"keyword": city, "max": 1},
            timeout=10
        )
        city_res.raise_for_status()
        city_data = city_res.json().get("data", [])
        if not city_data:
            return f"City '{city}' not found in Amadeus."
        city_code = city_data[0]["iataCode"]

        hotels_res = requests.get(
            "https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-city",
            headers=headers,
            params={"cityCode": city_code, "ratings": "4,5"},
            timeout=10
        )
        hotels_res.raise_for_status()
        hotel_ids = [h["hotelId"] for h in hotels_res.json().get("data", [])[:50]]

        if not hotel_ids:
            return f"No hotels found in {city}."

        offers_res = requests.get(
            "https://test.api.amadeus.com/v3/shopping/hotel-offers",
            headers=headers,
            params={
                "hotelIds": ",".join(hotel_ids),
                "checkInDate": check_in,
                "checkOutDate": check_out,
                "adults": adults,
                "currency": "USD",
                "bestRateOnly": True
            },
            timeout=15
        )
        offers_res.raise_for_status()
        all_offers = offers_res.json().get("data", [])

        filtered = [
            o for o in all_offers
            if float(o["offers"][0]["price"]["total"]) <= budget
        ][:5]

        if not filtered:
            return f"No hotels available in {city} for those dates under ${budget}/night."

        results = []
        for offer in filtered:
            hotel = offer["hotel"]
            price_info = offer["offers"][0]["price"]
            results.append(
                f"• {hotel['name']} | "
                f"${price_info['total']}/night | "
                f"Rating: {hotel.get('rating', 'N/A')}★ | "
                f"Hotel ID: {hotel['hotelId']}"
            )

        logger.info(f"Amadeus: Found {len(results)} hotels")
        return "\n".join(results)

    except requests.exceptions.HTTPError as e:
        logger.error(f"Amadeus HTTP error: {e}")
        return f"Amadeus API error: {str(e)}"
    except Exception as e:
        logger.error(f"Amadeus search failed: {e}")
        return f"Hotel search failed: {str(e)}"


def verify_hotel_amadeus(hotel_id: str, check_in: str, check_out: str, adults: int = 1) -> dict:
    """
    Verify real-time availability and price for ONE specific hotel.
    Called by the /verify endpoint — NOT a LangChain tool.
    Returns a dict with availability, current price, and booking link.
    """
    try:
        logger.info(f"Amadeus verify: {hotel_id}, {check_in} to {check_out}")

        token = _get_amadeus_token()
        headers = {"Authorization": f"Bearer {token}"}

        offers_res = requests.get(
            "https://test.api.amadeus.com/v3/shopping/hotel-offers",
            headers=headers,
            params={
                "hotelIds": hotel_id,
                "checkInDate": check_in,
                "checkOutDate": check_out,
                "adults": adults,
                "currency": "USD",
                "bestRateOnly": True
            },
            timeout=15
        )
        offers_res.raise_for_status()
        data = offers_res.json().get("data", [])

        if not data:
            return {
                "available": False,
                "hotel_id": hotel_id,
                "message": "No availability found for these dates."
            }

        offer = data[0]
        hotel = offer["hotel"]
        price_info = offer["offers"][0]["price"]
        offer_id = offer["offers"][0]["id"]

        # Build Amadeus booking link
        booking_link = f"https://test.api.amadeus.com/v3/shopping/hotel-offers/{offer_id}"

        return {
            "available": True,
            "hotel_id": hotel_id,
            "hotel_name": hotel.get("name", ""),
            "current_price": float(price_info["total"]),
            "currency": price_info.get("currency", "USD"),
            "offer_id": offer_id,
            "booking_link": booking_link,
            "check_in": check_in,
            "check_out": check_out,
            "message": "Available"
        }

    except requests.exceptions.HTTPError as e:
        logger.error(f"Amadeus verify HTTP error: {e}")
        return {"available": False, "hotel_id": hotel_id, "message": str(e)}
    except Exception as e:
        logger.error(f"Amadeus verify failed: {e}")
        return {"available": False, "hotel_id": hotel_id, "message": str(e)}