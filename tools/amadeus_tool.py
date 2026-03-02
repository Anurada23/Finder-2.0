from langchain_core.tools import tool
from config import settings
from utils import logger
import requests


def _get_amadeus_token() -> str:
    """Get Amadeus OAuth token"""
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

    Args:
        city: City name (e.g., 'Paris')
        check_in: Check-in date in YYYY-MM-DD format
        check_out: Check-out date in YYYY-MM-DD format
        budget: Maximum price per night in USD
        adults: Number of adults (default 1)
    """
    try:
        logger.info(f"Amadeus hotel search: {city}, {check_in} to {check_out}, budget ${budget}")

        token = _get_amadeus_token()
        headers = {"Authorization": f"Bearer {token}"}

        # Step 1: Get city IATA code
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

        # Step 2: Get hotel IDs in that city (4-5 star only)
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

        # Step 3: Get live offers and pricing
        offers_res = requests.get(
            "https://test.api.amadeus.com/v3/shopping/hotel-offers",
            headers=headers,
            params={
                "hotelIds": ",".join(hotel_ids),
                "checkInDate": check_in,
                "checkOutDate": check_out,
                "adults": adults,
                #"priceRange": f"1-{int(budget)}",
                "currency": "USD",
                "bestRateOnly": True
            },
            timeout=15
        )
        offers_res.raise_for_status()
        offers = offers_res.json().get("data", [])[:5]  # TOP 5 ONLY

        # Filter by budget manually
        filtered = [
            o for o in offers
            if float(o["offers"][0]["price"]["total"]) <= budget
        ][:5]

        if not offers:
            return f"No hotels available in {city} for those dates under ${budget}/night."

        results = []
        for offer in offers:
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