# 🏨 Hotel Booking System - Complete Guide

## 🎉 What's New

Your Finder AI has been upgraded with **hotel booking capabilities**! Now it can:

✅ Search hotels across multiple platforms
✅ Compare prices automatically
✅ Find reviews and ratings
✅ Make intelligent recommendations
✅ Remember your preferences
✅ Automate booking workflows with n8n

---

## 🚀 Quick Start

### 1. Start the Backend

```powershell
cd "D:\VsCode Projects\Finder 2.0"
python run.py
```

### 2. Start the Frontend

```powershell
# New terminal
cd "D:\VsCode Projects\Finder 2.0"
python -m http.server 3000
```

### 3. Access the Hotel Booking Interface

Open in browser:
- **Hotel Booking:** http://localhost:3000/frontend/hotel.html
- **Chat Interface:** http://localhost:3000/frontend/index.html
- **API Docs:** http://localhost:8000/docs

---

## 🆕 New Features

### **1. Hotel Search Tools**

Three new AI tools have been added:

#### `search_hotels`
Searches for hotels based on criteria:
- Location
- Check-in/Check-out dates
- Budget
- Number of guests
- Preferences (pool, beach, breakfast, etc.)

#### `compare_hotel_prices`
Compares prices for a specific hotel across:
- Booking.com
- Hotels.com
- Expedia
- Agoda

#### `get_hotel_reviews`
Gets reviews and ratings from:
- TripAdvisor
- Google Reviews
- Booking platforms

### **2. New API Endpoints**

#### Search Hotels
```bash
POST /api/v2/hotels/search

{
  "location": "Paris",
  "checkin": "2026-04-15",
  "checkout": "2026-04-18",
  "budget": "$200",
  "guests": 2,
  "preferences": "breakfast included"
}
```

#### Compare Prices
```bash
POST /api/v2/hotels/compare

{
  "hotel_name": "Hotel Le Marais",
  "location": "Paris"
}
```

#### Get Search History
```bash
GET /api/v2/hotels/searches/{session_id}
```

### **3. New Database Tables**

Three new Snowflake tables:

**hotel_searches** - Search requests
**hotel_results** - Search results
**hotel_bookings** - Confirmed bookings

### **4. New Frontend Pages**

**hotel.html** - Dedicated hotel booking interface with:
- Search form
- Results display
- Quick search examples
- Responsive design

---

## 💻 How to Use

### **Option 1: Use the Chat Interface**

Go to: http://localhost:3000/frontend/index.html

Try these queries:
```
"Find hotels in Paris under $200 for 3 nights"
"Best beach hotels in Bali for 2 people"
"Compare prices for Hilton Tokyo"
"Hotels near Eiffel Tower with breakfast"
```

### **Option 2: Use the Hotel Booking Form**

Go to: http://localhost:3000/frontend/hotel.html

1. Fill in the form:
   - Destination
   - Dates
   - Budget
   - Preferences

2. Click "Search Hotels"

3. AI agents will:
   - Search multiple platforms
   - Compare prices
   - Read reviews
   - Provide recommendations

---

## 🤖 How the Multi-Agent System Works

When you search for hotels:

### **Step 1: Memory Agent** 🧠
- Checks if you've searched before
- Remembers your preferences
- Uses past budget ranges

### **Step 2: Planner Agent** 📋
- Analyzes your query
- Creates search strategy
- Decides which tools to use

### **Step 3: Researcher Agent** 🔍
- Uses `search_hotels` tool
- Searches Booking.com, Hotels.com, etc.
- Visits hotel websites
- Extracts prices and reviews
- Uses `compare_hotel_prices` if needed
- Uses `get_hotel_reviews` for ratings

### **Step 4: Synthesizer Agent** ✍️
- Combines all findings
- Ranks hotels by value
- Formats recommendations
- Cites sources

---

## 📊 Example Workflow

**User Input:**
```
Location: Tokyo
Check-in: 2026-05-01
Check-out: 2026-05-05
Budget: $150/night
Preferences: Near Shibuya, breakfast
```

**What Happens:**

1. **Memory Agent:** "User prefers mid-range hotels"

2. **Planner Agent:** Creates plan:
   - Search Tokyo hotels near Shibuya
   - Filter by $150 budget
   - Check breakfast amenities
   - Compare top 3 options

3. **Researcher Agent:** Executes:
   - Searches "hotels Tokyo Shibuya under $150"
   - Visits Booking.com, Hotels.com results
   - Checks reviews for top hotels
   - Compares prices across platforms

4. **Synthesizer Agent:** Produces:
   ```
   Top 3 Hotels in Tokyo (Shibuya Area)
   
   1. Hotel Sunroute Plaza Shinjuku
      - $145/night (Booking.com best price)
      - ⭐ 4.5/5 (2,100 reviews)
      - ✅ Breakfast included
      - 📍 10 min walk to Shibuya station
      
   2. Shibuya Granbell Hotel
      - $149/night (Hotels.com)
      - ⭐ 4.6/5 (1,800 reviews)
      - ✅ Breakfast buffet
      - 📍 5 min to Shibuya crossing
      
   [... more options ...]
   ```

---

## 🔗 n8n Integration

### **What n8n Can Do:**

1. **Automated Daily Deals**
   - Schedule: Check hotel prices daily
   - If price drops → Alert you
   - Track price trends

2. **Email Notifications**
   - Search completed → Email summary
   - Include booking links
   - Formatted recommendations

3. **Booking Follow-ups**
   - User searches but doesn't book
   - Wait 24 hours
   - Send reminder with updated prices

4. **Multi-Platform Comparison**
   - Search hotel on Finder AI
   - Automatically check other platforms
   - Find lowest price
   - Generate comparison report

### **Setup n8n Workflow:**

1. **Import workflow:**
   ```bash
   # In n8n, import:
   n8n/hotel-booking-workflow.json
   ```

2. **Configure:**
   - Set webhook URL
   - Add your email (optional)
   - Connect Google Sheets (optional)
   - Connect Slack (optional)

3. **Test:**
   ```bash
   curl -X POST http://localhost:5678/webhook/hotel-booking \
     -H "Content-Type: application/json" \
     -d '{
       "location": "Paris",
       "budget": "$200",
       "checkin": "2026-04-15",
       "checkout": "2026-04-18"
     }'
   ```

---

## 📈 Snowflake Analytics

### **Query Popular Destinations:**

```sql
SELECT 
    location,
    COUNT(*) as search_count,
    AVG(budget) as avg_budget
FROM hotel_searches
WHERE created_at >= DATEADD(day, -30, CURRENT_TIMESTAMP())
GROUP BY location
ORDER BY search_count DESC
LIMIT 10;
```

### **Price Trends:**

```sql
SELECT 
    hotel_name,
    AVG(price_per_night) as avg_price,
    COUNT(*) as times_found
FROM hotel_results
WHERE created_at >= DATEADD(day, -7, CURRENT_TIMESTAMP())
GROUP BY hotel_name
ORDER BY times_found DESC;
```

### **Booking Conversion Rate:**

```sql
SELECT 
    COUNT(DISTINCT search_id) as total_searches,
    COUNT(DISTINCT booking_id) as total_bookings,
    (COUNT(DISTINCT booking_id) * 100.0 / COUNT(DISTINCT search_id)) as conversion_rate
FROM hotel_searches
LEFT JOIN hotel_bookings USING (search_id)
WHERE hotel_searches.created_at >= DATEADD(day, -30, CURRENT_TIMESTAMP());
```

---

## 🎨 Customization

### **Add More Hotel Platforms:**

Edit `tools/hotel_tools.py`:

```python
# Add more platforms
platforms = [
    "booking.com",
    "hotels.com",
    "expedia.com",
    "agoda.com",
    "airbnb.com",  # Add this
    "vrbo.com"      # Add this
]
```

### **Customize Search Prompts:**

Edit `config/prompts.py`:

```python
RESEARCHER_PROMPT = """...
For hotels:
- Focus on value for money
- Prioritize verified reviews
- Check cancellation policies
- Note hidden fees
..."""
```

### **Change Frontend Styling:**

Edit `frontend/css/hotel.css` to match your brand.

---

## 🐛 Troubleshooting

### **Hotels Not Found:**

- Check if location is specific enough
- Try different spelling (e.g., "NYC" vs "New York")
- Verify internet connection
- Check Groq API limits

### **Slow Searches:**

- Normal: 20-30 seconds for thorough research
- If >1 minute: Check internet speed
- Reduce number of searches in code

### **Price Comparison Not Working:**

- Some hotels block automated scraping
- Try official booking platform APIs
- Consider RapidAPI for structured data

---

## 🚀 Future Enhancements

### **Phase 1 (Current):**
✅ Multi-agent hotel search
✅ Price comparison
✅ Review aggregation
✅ n8n integration

### **Phase 2 (Next):**
- [ ] Direct booking integration
- [ ] Payment processing (Stripe)
- [ ] User accounts & saved searches
- [ ] Price alerts
- [ ] Mobile app

### **Phase 3 (Advanced):**
- [ ] ML-based price prediction
- [ ] Personalized recommendations
- [ ] Loyalty program integration
- [ ] Group bookings
- [ ] Travel package bundles

---

## 📞 Support

**Having Issues?**

1. Check logs in Terminal 1
2. Verify Snowflake connection
3. Test API: http://localhost:8000/docs
4. Check browser console (F12)

**Need Features?**

Open an issue or contact the team!

---

## 🎉 Summary

**What You Can Do Now:**

✅ Search hotels with AI
✅ Compare prices automatically
✅ Get intelligent recommendations
✅ Automate with n8n
✅ Track searches in Snowflake
✅ Use chat or form interface

**Happy Booking! 🏨✈️**