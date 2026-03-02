"""SQL queries for Snowflake operations"""

# Research Sessions
INSERT_RESEARCH_SESSION = """
INSERT INTO research_sessions (
    session_id, user_query, agent_response, research_plan, 
    sources_used, tokens_used, cost
) VALUES (%s, %s, %s, %s, %s, %s, %s)
"""

GET_RESEARCH_SESSION = """
SELECT * FROM research_sessions 
WHERE session_id = %s
"""

GET_RECENT_SESSIONS = """
SELECT * FROM research_sessions 
ORDER BY created_at DESC 
LIMIT %s
"""

# Conversation History
INSERT_CONVERSATION_MESSAGE = """
INSERT INTO conversation_history (
    id, session_id, role, content, metadata
) VALUES (%s, %s, %s, %s, %s)
"""

GET_CONVERSATION_HISTORY = """
SELECT * FROM conversation_history 
WHERE session_id = %s 
ORDER BY created_at ASC
"""

DELETE_OLD_CONVERSATIONS = """
DELETE FROM conversation_history 
WHERE created_at < DATEADD(day, -%s, CURRENT_TIMESTAMP())
"""

# Agent Traces
INSERT_AGENT_TRACE = """
INSERT INTO agent_traces (
    id, session_id, agent_name, action, result, duration_ms
) VALUES (%s, %s, %s, %s, %s, %s)
"""

GET_AGENT_TRACES = """
SELECT * FROM agent_traces 
WHERE session_id = %s 
ORDER BY created_at ASC
"""

# Hotel Searches
INSERT_HOTEL_SEARCH = """
INSERT INTO hotel_searches (
    search_id, session_id, user_id, location, checkin_date, 
    checkout_date, guests, budget, preferences
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

GET_HOTEL_SEARCH = """
SELECT * FROM hotel_searches 
WHERE search_id = %s
"""

GET_USER_HOTEL_SEARCHES = """
SELECT * FROM hotel_searches 
WHERE user_id = %s 
ORDER BY created_at DESC 
LIMIT %s
"""

# Hotel Results
INSERT_HOTEL_RESULT = """
INSERT INTO hotel_results (
    result_id, search_id, hotel_name, price_per_night, total_price,
    rating, platform, booking_url, amenities, location_details
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

GET_HOTEL_RESULTS = """
SELECT * FROM hotel_results 
WHERE search_id = %s 
ORDER BY price_per_night ASC
"""

GET_BEST_HOTEL_DEALS = """
SELECT * FROM hotel_results 
WHERE search_id = %s 
  AND rating >= %s
ORDER BY price_per_night ASC 
LIMIT %s
"""

# Hotel Bookings
INSERT_HOTEL_BOOKING = """
INSERT INTO hotel_bookings (
    booking_id, search_id, user_id, hotel_name, checkin_date,
    checkout_date, guests, total_price, booking_status, 
    confirmation_code, payment_status
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

UPDATE_BOOKING_STATUS = """
UPDATE hotel_bookings 
SET booking_status = %s, updated_at = CURRENT_TIMESTAMP()
WHERE booking_id = %s
"""

GET_USER_BOOKINGS = """
SELECT * FROM hotel_bookings 
WHERE user_id = %s 
ORDER BY created_at DESC
"""

GET_BOOKING_BY_ID = """
SELECT * FROM hotel_bookings 
WHERE booking_id = %s
"""

# Analytics Queries
GET_QUERY_STATS = """
SELECT 
    COUNT(*) as total_queries,
    AVG(tokens_used) as avg_tokens,
    AVG(cost) as avg_cost,
    MIN(created_at) as first_query,
    MAX(created_at) as last_query
FROM research_sessions
WHERE created_at >= DATEADD(day, -%s, CURRENT_TIMESTAMP())
"""

GET_TOP_QUERIES = """
SELECT 
    user_query,
    COUNT(*) as frequency
FROM research_sessions
WHERE created_at >= DATEADD(day, -%s, CURRENT_TIMESTAMP())
GROUP BY user_query
ORDER BY frequency DESC
LIMIT %s
"""

GET_AGENT_PERFORMANCE = """
SELECT 
    agent_name,
    COUNT(*) as total_actions,
    AVG(duration_ms) as avg_duration_ms
FROM agent_traces
WHERE created_at >= DATEADD(day, -%s, CURRENT_TIMESTAMP())
GROUP BY agent_name
ORDER BY total_actions DESC
"""

# Hotel Analytics
GET_POPULAR_DESTINATIONS = """
SELECT 
    location,
    COUNT(*) as search_count,
    AVG(budget) as avg_budget
FROM hotel_searches
WHERE created_at >= DATEADD(day, -%s, CURRENT_TIMESTAMP())
GROUP BY location
ORDER BY search_count DESC
LIMIT %s
"""

GET_BOOKING_STATS = """
SELECT 
    COUNT(*) as total_bookings,
    SUM(total_price) as total_revenue,
    AVG(total_price) as avg_booking_value
FROM hotel_bookings
WHERE created_at >= DATEADD(day, -%s, CURRENT_TIMESTAMP())
  AND booking_status = 'confirmed'
"""