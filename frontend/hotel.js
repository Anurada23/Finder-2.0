// ── AUELIA Hotel JS ──
let currentSessionId = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeSession();
    setupEventListeners();
    setMinDates();
});

// ── SESSION ──
function initializeSession() {
    currentSessionId = 'hotel_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    const sessionDisplay = document.getElementById('session-id');
    if (sessionDisplay) {
        sessionDisplay.textContent = `Session: ${currentSessionId.substr(0, 20)}...`;
    }
}

// ── EVENT LISTENERS ──
function setupEventListeners() {
    const form = document.getElementById('hotel-search-form');
    if (form) form.addEventListener('submit', handleHotelSearch);
}

// ── DATE SETUP ──
function setMinDates() {
    const today = new Date().toISOString().split('T')[0];
    const checkinInput = document.getElementById('checkin');
    const checkoutInput = document.getElementById('checkout');

    if (checkinInput) {
        checkinInput.min = today;
        checkinInput.addEventListener('change', () => {
            if (checkoutInput) checkoutInput.min = checkinInput.value;
        });
    }
}

// ── MAIN SEARCH HANDLER ──
async function handleHotelSearch(e) {
    e.preventDefault();

    const location    = document.getElementById('location').value.trim();
    const checkin     = document.getElementById('checkin').value;
    const checkout    = document.getElementById('checkout').value;
    const guests      = document.getElementById('guests').value;
    const budget      = document.getElementById('budget').value.trim();
    const preferences = document.getElementById('preferences').value.trim();

    if (!location) {
        alert('Please enter a destination');
        return;
    }

    setLoading(true);
    showResults();
    showLoadingCard();

    try {
        const response = await fetch('http://127.0.0.1:8000/api/v2/hotels/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                location,
                checkin:     checkin     || null,
                checkout:    checkout    || null,
                guests:      parseInt(guests),
                budget:      budget      || null,
                preferences: preferences || null,
                session_id:  currentSessionId
            })
        });

        if (!response.ok) throw new Error(`Server error: ${response.status}`);

        const data = await response.json();
        displayResults(data);

    } catch (error) {
        console.error('Hotel search error:', error);
        showError(error.message);
    } finally {
        setLoading(false);
    }
}

// ── QUICK SEARCH ──
function quickSearch(location, budget) {
    document.getElementById('location').value = location;
    document.getElementById('budget').value = `$${budget}`;
    document.getElementById('hotel-search-form').scrollIntoView({ behavior: 'smooth' });
}

// ── SHOW / HIDE RESULTS ──
function showResults() {
    const resultsSection = document.getElementById('results-section');
    if (resultsSection) {
        resultsSection.classList.add('visible');
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

// ── LOADING CARD ──
function showLoadingCard() {
    const container = document.getElementById('results-container');
    if (!container) return;
    container.innerHTML = `
        <div class="loading-card">
            <div class="loading-crest">✦</div>
            <div class="loading-text">Curating your selection…</div>
        </div>
    `;
}

// ── DISPLAY RESULTS ──
function displayResults(data) {
    const container = document.getElementById('results-container');
    const countEl   = document.getElementById('results-count');
    if (!container) return;

    const hotels = parseHotelsFromResponse(data.response);

    if (countEl) {
        countEl.textContent = hotels.length > 0
            ? `${hotels.length} propert${hotels.length === 1 ? 'y' : 'ies'} found`
            : '';
    }

    // No structured hotels parsed — show raw AI response
    if (hotels.length === 0) {
        container.innerHTML = `
            <div class="ai-card">
                <div class="ai-card-head">
                    <div class="ai-icon">✦</div>
                    <span class="ai-label">Auelia Intelligence</span>
                </div>
                <div class="ai-content">${escapeHtml(data.response)}</div>
            </div>
        `;
        return;
    }

    // AI summary card (first line of response)
    const summaryLine = data.response.split('\n').find(l => l.trim() && !l.trim().startsWith('•')) || '';

    const cardsHtml = hotels.map((hotel, index) => `
        <div class="hotel-card" style="animation-delay: ${0.05 + index * 0.07}s">
            <div class="card-body">
                <div class="hotel-rank">0${index + 1}</div>
                <div class="hotel-name">${escapeHtml(hotel.name)}</div>
                <div class="hotel-location">${escapeHtml(hotel.location)}</div>
                <div class="hotel-stars">${renderStars(hotel.stars)}</div>
                ${hotel.description
                    ? `<div class="hotel-description">${escapeHtml(hotel.description)}</div>`
                    : ''}
                ${hotel.amenities.length > 0 ? `
                    <div class="amenities-row">
                        ${hotel.amenities.map(a => `<span class="amenity-tag">${escapeHtml(a)}</span>`).join('')}
                    </div>` : ''}
            </div>
            <div class="card-aside">
                <div class="price-block">
                    <div class="price-from">From</div>
                    <div class="price-amount">
                        <span class="price-currency">$</span>${escapeHtml(hotel.price)}
                    </div>
                    <div class="price-per">per night</div>
                </div>
                <div class="card-rating">
                    <span class="rating-num">${escapeHtml(hotel.rating)}</span>
                    ${hotel.rating !== 'N/A' ? '/ 5' : ''}
                </div>
                <button class="book-btn" onclick="handleBook('${escapeAttr(hotel.name)}', '${escapeAttr(hotel.hotelId)}')">
                    Reserve Now
                </button>
                <button class="details-btn" onclick="handleDetails('${escapeAttr(hotel.name)}', '${escapeAttr(hotel.hotelId)}')">
                    View Details
                </button>
            </div>
        </div>
    `).join('');

    container.innerHTML = `
        ${summaryLine ? `
        <div class="ai-card" style="margin-bottom: 30px;">
            <div class="ai-card-head">
                <div class="ai-icon">✦</div>
                <span class="ai-label">Auelia Intelligence</span>
            </div>
            <div class="ai-content">${escapeHtml(summaryLine)}</div>
        </div>` : ''}
        ${cardsHtml}
    `;
}

// ── PARSE HOTELS FROM AI RESPONSE ──
// Expects lines like: • Hotel Name | $120/night | Rating: 4★ | Hotel ID: XXXXX
function parseHotelsFromResponse(responseText) {
    const hotels = [];
    const lines = responseText.split('\n').filter(l => /^[\d]+\.|^[•\-]/.test(l.trim()));

    lines.forEach(line => {
        // Remove leading number/bullet: "1. **Hotel Name**"
        const cleaned = line.replace(/^\d+\.\s*/, '').replace(/\*\*/g, '').trim();

        // Split by " – " or " | "
        const parts = cleaned.split(/\s[–—|]\s/);
        if (parts.length < 2) return;

        const name = parts[0].trim();

        // Price
        const priceMatch = cleaned.match(/\$([\d,]+(?:\.\d{1,2})?)/);
        const price = priceMatch ? priceMatch[1] : '—';

        // Rating
        const ratingMatch = cleaned.match(/Rating[:\s]*([\d.]+)/i);
        const rating = ratingMatch ? ratingMatch[1] : 'N/A';
        const stars = Math.min(5, Math.max(1, Math.round(parseFloat(rating) || 4)));

        // Description — italic text between * *
        const descMatch = line.match(/\*([^*]+)\*/);
        const description = descMatch ? descMatch[1].trim() : '';

        hotels.push({
            name,
            price,
            rating,
            stars,
            hotelId: '',
            location: 'Paris, France',
            description,
            amenities: []
        });
    });

    return hotels;
}

// ── STARS RENDERER ──
function renderStars(count) {
    const filled = Math.min(5, Math.max(0, count));
    return '★'.repeat(filled) + '☆'.repeat(5 - filled);
}

// ── BOOK HANDLER ──
function handleBook(hotelName, hotelId) {
    // TODO: Wire to n8n booking workflow
    alert(`Booking flow coming soon!\n\n${hotelName}\nHotel ID: ${hotelId}`);
}

// ── DETAILS HANDLER ──
function handleDetails(hotelName, hotelId) {
    // TODO: Open detail modal or navigate to detail page
    alert(`Details view coming soon!\n\n${hotelName}\nHotel ID: ${hotelId}`);
}

// ── ERROR DISPLAY ──
function showError(message) {
    const container = document.getElementById('results-container');
    if (!container) return;
    container.innerHTML = `
        <div class="ai-card" style="border-color: #c0392b;">
            <div class="ai-card-head">
                <div class="ai-icon" style="border-color:#c0392b; color:#c0392b;">✕</div>
                <span class="ai-label" style="color:#c0392b;">Search Failed</span>
            </div>
            <div class="ai-content" style="color: rgba(247,242,236,0.7);">${escapeHtml(message)}</div>
            <button class="book-btn" style="margin-top: 20px; width: auto; padding: 12px 30px;"
                onclick="location.reload()">Try Again</button>
        </div>
    `;
}

// ── LOADING STATE ──
function setLoading(isLoading) {
    const btn = document.getElementById('search-btn');
    if (!btn) return;
    btn.disabled = isLoading;
    btn.classList.toggle('loading', isLoading);
}

// ── UTILITIES ──
function escapeHtml(text) {
    if (text == null) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

function escapeAttr(text) {
    if (text == null) return '';
    return String(text).replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

function formatPrice(price) {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(price);
}

function calculateNights(checkin, checkout) {
    if (!checkin || !checkout) return 0;
    const diff = new Date(checkout) - new Date(checkin);
    return Math.ceil(diff / (1000 * 60 * 60 * 24));
}