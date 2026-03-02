from langchain_core.tools import tool
from tools.search_tool import search_web
from tools.visit_website import visit_website
from utils import logger
from datetime import datetime, timedelta
import re


@tool
def search_hotels(
    location: str, 
    checkin: str = "", 
    checkout: str = "", 
    budget: str = "", 
    guests: int = 2,
    preferences: str = ""
) -> str:
    """
    Search for hotels based on user criteria. OPTIMIZED for TOP 5 results.
    
    Args:
        location: City or area to search for hotels
        checkin: Check-in date (YYYY-MM-DD format or natural language like "next week")
        checkout: Check-out date (YYYY-MM-DD format or natural language)
        budget: Maximum price per night (e.g., "$200", "under 150")
        guests: Number of guests
        preferences: Additional preferences (beach, pool, breakfast, etc.)
        
    Returns:
        Hotel search results with prices, ratings, and booking information (TOP 5 ONLY)
    """
    try:
        logger.info(f"Hotel search: {location}, {checkin}-{checkout}, budget: {budget}")
        
        # Build comprehensive search query
        query_parts = [f"best hotels in {location}"]
        
        if checkin and checkout:
            query_parts.append(f"from {checkin} to {checkout}")
        
        if budget:
            # Extract price from budget string
            price_match = re.search(r'\d+', str(budget))
            if price_match:
                query_parts.append(f"under ${price_match.group()}")
        
        if preferences:
            query_parts.append(preferences)
        
        # Create main search query
        main_query = " ".join(query_parts)
        
        # OPTIMIZED: Only 2 searches for speed
        searches = []
        searches.append(f"top 5 {main_query}")
        searches.append(f"{main_query} booking.com")
        
        # Execute searches - LIMITED TO 2
        results = []
        for search_query in searches[:2]:  # HARD LIMIT: 2 searches only
            logger.info(f"Searching: {search_query}")
            search_result = search_web.invoke(search_query)
            results.append(f"Search '{search_query}':\n{search_result}\n")
        
        combined_results = "\n".join(results)
        
        # Add helpful context
        summary = f"""
Hotel Search Results for {location} (TOP 5 HOTELS)
Check-in: {checkin or 'Not specified'}
Check-out: {checkout or 'Not specified'}
Budget: {budget or 'Not specified'}
Guests: {guests}
Preferences: {preferences or 'None'}

{combined_results}

Note: Focus on TOP 5 hotels by rating and value. Prices should be verified on booking platforms.
        """
        
        return summary.strip()
        
    except Exception as e:
        error_msg = f"Hotel search failed: {str(e)}"
        logger.error(error_msg)
        return error_msg


@tool
def compare_hotel_prices(hotel_name: str, location: str) -> str:
    """
    Compare prices for a specific hotel across different booking platforms.
    
    Args:
        hotel_name: Name of the hotel
        location: City/location of the hotel
        
    Returns:
        Price comparison across platforms
    """
    try:
        logger.info(f"Comparing prices for: {hotel_name} in {location}")
        
        platforms = [
            "booking.com",
            "hotels.com",
            "expedia.com",
            "agoda.com"
        ]
        
        results = []
        for platform in platforms:
            query = f"{hotel_name} {location} price {platform}"
            logger.info(f"Checking: {query}")
            result = search_web.invoke(query)
            results.append(f"{platform}:\n{result}\n")
        
        comparison = f"""
Price Comparison for {hotel_name}, {location}
{'='*60}

{chr(10).join(results)}

Tip: Prices may vary by date. Always check directly on the platform for the most accurate rates.
        """
        
        return comparison.strip()
        
    except Exception as e:
        error_msg = f"Price comparison failed: {str(e)}"
        logger.error(error_msg)
        return error_msg


@tool
def get_hotel_reviews(hotel_name: str, location: str) -> str:
    """
    Get reviews and ratings for a specific hotel.
    
    Args:
        hotel_name: Name of the hotel
        location: City/location
        
    Returns:
        Review summary and ratings
    """
    try:
        logger.info(f"Getting reviews for: {hotel_name} in {location}")
        
        # Search for reviews on multiple platforms
        queries = [
            f"{hotel_name} {location} reviews tripadvisor",
            f"{hotel_name} {location} google reviews",
            f"{hotel_name} {location} rating"
        ]
        
        results = []
        for query in queries:
            logger.info(f"Searching reviews: {query}")
            result = search_web.invoke(query)
            results.append(result)
        
        review_summary = f"""
Reviews for {hotel_name}, {location}
{'='*60}

{chr(10).join(results)}

Summary: Check multiple platforms for balanced perspective.
        """
        
        return review_summary.strip()
        
    except Exception as e:
        error_msg = f"Review search failed: {str(e)}"
        logger.error(error_msg)
        return error_msg