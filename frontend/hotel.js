// ── AUELIA Hotel JS ──
let currentSessionId   = null;
let lastSearchCheckin  = null;
let lastSearchCheckout = null;
let lastSearchCity     = null;

document.addEventListener('DOMContentLoaded', () => {
    initializeSession();
    setupEventListeners();
    setMinDates();
});

function initializeSession() {
    currentSessionId = 'hotel_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    const el = document.getElementById('session-id');
    if (el) el.textContent = `Session: ${currentSessionId.substr(0, 20)}...`;
}

function setupEventListeners() {
    const form = document.getElementById('hotel-search-form');
    if (form) form.addEventListener('submit', handleHotelSearch);
}

function setMinDates() {
    const today = new Date().toISOString().split('T')[0];
    const ci    = document.getElementById('checkin');
    const co    = document.getElementById('checkout');
    if (ci) {
        ci.min = today;
        ci.addEventListener('change', () => { if (co) co.min = ci.value; });
    }
}

async function handleHotelSearch(e) {
    e.preventDefault();

    const location    = document.getElementById('location').value.trim();
    const checkin     = document.getElementById('checkin').value;
    const checkout    = document.getElementById('checkout').value;
    const guests      = document.getElementById('guests').value;
    const budget      = document.getElementById('budget').value.trim();
    const preferences = document.getElementById('preferences').value.trim();

    if (!location) { alert('Please enter a destination'); return; }

    // Store for verify calls
    lastSearchCheckin  = checkin  || null;
    lastSearchCheckout = checkout || null;
    lastSearchCity     = location;  // ← store city for verify

    setLoading(true);
    showResults();
    showLoadingCard();

    try {
        const res = await fetch('http://127.0.0.1:8000/api/v2/hotels/search', {
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

        if (!res.ok) throw new Error(`Server error: ${res.status}`);
        const data = await res.json();
        displayResults(data, location);

    } catch (err) {
        console.error('Search error:', err);
        showError(err.message);
    } finally {
        setLoading(false);
    }
}

function quickSearch(location, budget) {
    document.getElementById('location').value = location;
    document.getElementById('budget').value   = `$${budget}`;
    document.getElementById('hotel-search-form').scrollIntoView({ behavior: 'smooth' });
}

function showResults() {
    const s = document.getElementById('results-section');
    if (s) {
        s.classList.add('visible');
        s.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

function showLoadingCard() {
    const c = document.getElementById('results-container');
    if (!c) return;
    c.innerHTML = `
        <div class="loading-card">
            <div class="loading-crest">✦</div>
            <div class="loading-text">Curating your selection…</div>
        </div>`;
}

function displayResults(data, location) {
    const container = document.getElementById('results-container');
    const countEl   = document.getElementById('results-count');
    if (!container) return;

    const hotels = parseHotelsFromResponse(data.response);

    if (countEl) {
        countEl.textContent = hotels.length > 0
            ? `${hotels.length} propert${hotels.length === 1 ? 'y' : 'ies'} found`
            : '';
    }

    if (hotels.length === 0) {
        container.innerHTML = `
            <div class="ai-card">
                <div class="ai-card-head">
                    <div class="ai-icon">✦</div>
                    <span class="ai-label">Auelia Intelligence</span>
                </div>
                <div class="ai-content">${escapeHtml(data.response)}</div>
            </div>`;
        return;
    }

    const cardsHtml = hotels.map((hotel, i) => buildHotelCard(hotel, i, location)).join('');
    container.innerHTML = cardsHtml;
}

function buildHotelCard(hotel, index, location) {
    const cardId = `card-${index}`;
    return `
        <div class="hotel-card" id="${cardId}" style="animation-delay:${0.05 + index * 0.07}s; flex-direction:column;">
            <div style="display:grid; grid-template-columns:1fr auto;">
                <div class="card-body">
                    <div class="hotel-rank">0${index + 1}</div>
                    <div class="hotel-name">${escapeHtml(hotel.name)}</div>
                    <div class="hotel-location">${escapeHtml(hotel.location || location || '')}</div>
                    <div class="hotel-stars">${renderStars(hotel.stars)}</div>
                    ${hotel.description
                        ? `<div class="hotel-description">${escapeHtml(hotel.description)}</div>`
                        : ''}
                </div>
                <div class="card-aside">
                    <div class="price-block">
                        <div class="price-from">From</div>
                        <div class="price-amount" id="${cardId}-price">
                            <span class="price-currency">$</span>${escapeHtml(hotel.price)}
                        </div>
                        <div class="price-per">per night</div>
                    </div>
                    <div class="card-rating">
                        <span class="rating-num">${escapeHtml(hotel.rating)}</span>
                        ${hotel.rating !== 'N/A' ? '/ 5' : ''}
                    </div>
                    <button class="details-btn" style="margin-top:16px;"
                        id="${cardId}-verify-btn"
                        onclick="handleVerify('${cardId}', '${escapeAttr(hotel.name)}', ${parseFloat(hotel.price) || 0})">
                        ◎ Check Live Price
                    </button>
                </div>
            </div>
            <div id="${cardId}-live" style="display:none; border-top:1px solid rgba(201,168,76,0.15); padding:24px 36px; background:rgba(247,242,236,0.4);"></div>
        </div>`;
}

// ── VERIFY — now sends hotel_name + city instead of hotel_id ──
async function handleVerify(cardId, hotelName, originalPrice) {
    const btn     = document.getElementById(`${cardId}-verify-btn`);
    const liveDiv = document.getElementById(`${cardId}-live`);
    if (!btn || !liveDiv) return;

    if (!lastSearchCheckin || !lastSearchCheckout) {
        liveDiv.style.display = 'block';
        liveDiv.innerHTML = `<span style="font-size:0.8rem; color:var(--muted);">
            Please enter check-in and check-out dates before verifying.</span>`;
        return;
    }

    btn.disabled    = true;
    btn.textContent = '◌ Checking via n8n…';
    liveDiv.style.display = 'block';
    liveDiv.innerHTML = `
        <div style="display:flex; align-items:center; gap:12px;">
            <div class="loading-crest" style="font-size:1.2rem; margin:0;">✦</div>
            <span style="font-size:0.72rem; letter-spacing:0.18em; text-transform:uppercase; color:var(--muted);">
                Verifying via n8n automation…
            </span>
        </div>`;

    try {
        const res = await fetch('http://127.0.0.1:8000/api/v2/hotels/verify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                hotel_name:     hotelName,
                city:           lastSearchCity,   // ← city instead of hotel_id
                checkin:        lastSearchCheckin,
                checkout:       lastSearchCheckout,
                original_price: originalPrice,
                adults:         2,
                session_id:     currentSessionId
            })
        });

        if (!res.ok) throw new Error(`Verify failed: ${res.status}`);
        const data = await res.json();
        renderLivePanel(cardId, data, originalPrice);

    } catch (err) {
        console.error('Verify error:', err);
        liveDiv.innerHTML = `
            <span style="font-size:0.8rem; color:#c0392b;">
                Could not verify availability. Please try again.
            </span>`;
        btn.disabled    = false;
        btn.textContent = '◎ Check Live Price';
    }
}

function renderLivePanel(cardId, data, originalPrice) {
    const liveDiv = document.getElementById(`${cardId}-live`);
    const btn     = document.getElementById(`${cardId}-verify-btn`);
    if (!liveDiv) return;

    if (!data.available) {
        liveDiv.innerHTML = `
            <div style="display:flex; align-items:center; gap:10px;">
                <span style="color:#c0392b;">✕</span>
                <span style="font-size:0.78rem; letter-spacing:0.12em; text-transform:uppercase; color:#c0392b;">
                    Not available for these dates
                </span>
            </div>`;
        btn.textContent = '✕ Unavailable';
        return;
    }

    let priceHtml = `
        <span style="font-family:'Cormorant Garamond',serif; font-size:1.8rem; color:var(--ink);">
            $${data.current_price ? data.current_price.toFixed(2) : originalPrice}
        </span>
        <span style="font-size:0.65rem; color:var(--muted); margin-left:6px;">/night</span>`;

    let changeHtml = '';
    if (data.price_changed) {
        const color  = data.price_direction === 'down' ? '#2ecc71' : '#c0392b';
        const symbol = data.price_direction === 'down' ? '↓' : '↑';
        const label  = data.price_direction === 'down' ? 'Price dropped!' : 'Price increased';
        changeHtml = `
            <span style="font-size:0.7rem; color:${color}; margin-left:10px;">
                ${symbol} $${data.price_diff.toFixed(2)} — ${label}
            </span>`;

        const priceEl = document.getElementById(`${cardId}-price`);
        if (priceEl) {
            priceEl.innerHTML = `
                <span style="text-decoration:line-through; opacity:0.4; font-size:1.4rem;">
                    <span class="price-currency">$</span>${originalPrice}
                </span>`;
        }
    }

    const sourceHtml = data.source === 'n8n'
        ? `<span style="color:var(--gold); font-size:0.6rem; letter-spacing:0.15em;">⚡ Verified via n8n Automation</span>`
        : `<span style="font-size:0.6rem; color:var(--muted);">Direct verify</span>`;

    const matchedNote = data.matched_name && data.matched_name !== data.hotel_name
        ? `<div style="font-size:0.62rem; color:var(--muted); margin-top:4px;">Matched to: ${escapeHtml(data.matched_name)}</div>`
        : '';

    const checkedAt = new Date(data.checked_at).toLocaleTimeString();

    liveDiv.innerHTML = `
        <div style="display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:16px;">
            <div>
                <div style="font-size:0.6rem; letter-spacing:0.2em; text-transform:uppercase; color:var(--muted); margin-bottom:6px;">
                    ✓ Available · Live Price
                </div>
                <div style="display:flex; align-items:baseline; flex-wrap:wrap; gap:4px;">
                    ${priceHtml}${changeHtml}
                </div>
                <div style="font-size:0.62rem; color:var(--muted); margin-top:6px;">
                    Checked at ${checkedAt} &nbsp;·&nbsp; ${sourceHtml}
                </div>
                ${matchedNote}
            </div>
            <div style="display:flex; flex-direction:column; gap:8px; min-width:160px;">
                <a href="https://www.booking.com/search.html?ss=${encodeURIComponent(data.hotel_name)}"
                   target="_blank" rel="noopener" class="book-btn"
                   style="text-align:center; text-decoration:none; display:block;">
                    View &amp; Book →
                </a>
                <button class="details-btn"
                    onclick="handleSelect('${escapeAttr(data.hotel_name)}', ${data.current_price || originalPrice}, '${cardId}')">
                    Select This Hotel
                </button>
            </div>
        </div>`;

    btn.textContent       = '✓ Verified';
    btn.style.borderColor = '#2ecc71';
    btn.style.color       = '#2ecc71';
    btn.disabled          = false;
}

function handleSelect(hotelName, price, cardId) {
    document.querySelectorAll('.hotel-card').forEach(c => {
        c.style.border = '1px solid rgba(201,168,76,0.15)';
    });
    const card = document.getElementById(cardId);
    if (card) card.style.border = '1px solid var(--gold)';

    const liveDiv = document.getElementById(`${cardId}-live`);
    if (liveDiv) {
        const existing = liveDiv.querySelector('.selection-confirm');
        if (!existing) {
            const confirm      = document.createElement('div');
            confirm.className  = 'selection-confirm';
            confirm.style.cssText = 'margin-top:16px; padding-top:16px; border-top:1px solid rgba(201,168,76,0.2); font-size:0.72rem; letter-spacing:0.15em; text-transform:uppercase; color:var(--gold);';
            confirm.textContent   = `✦ ${hotelName} selected at $${price.toFixed(2)}/night`;
            liveDiv.appendChild(confirm);
        }
    }
}

// ── PARSE — no Hotel ID needed anymore ──
function parseHotelsFromResponse(responseText) {
    const hotels = [];
    const lines  = responseText.split('\n').filter(l => {
        const t = l.trim();
        return t.startsWith('•') || t.startsWith('-') || /^\d+\./.test(t);
    });

    lines.forEach(line => {
        const cleaned = line
            .replace(/^\d+\.\s*/, '')
            .replace(/\*\*/g, '')
            .replace(/^[•\-\*]\s*/, '')
            .replace(/【\d+】/g, '')
            .trim();

        if (!cleaned || !/\$/.test(cleaned)) return;

        const nameMatch = cleaned.match(/^([^|–—$~≈]+)/);
        const name = nameMatch
            ? nameMatch[1].replace(/[-–—]\s*$/, '').trim()
            : 'Unknown Hotel';

        const priceMatch = cleaned.match(/[≈~]?\$([\d,]+(?:\.\d{1,2})?)/);
        const price = priceMatch ? priceMatch[1].replace(',', '') : '0';

        const ratingMatch = cleaned.match(/(\d+(?:\.\d+)?)\s*[★\/]/);
        const rating = ratingMatch ? ratingMatch[1] : 'N/A';
        const stars  = Math.min(5, Math.max(1, Math.round(parseFloat(rating) || 4)));

        const descMatch = line.match(/\*([^*]{15,})\*/);
        const description = descMatch ? descMatch[1].trim() : '';

        // No hotelId needed — name + city sent to verify instead
        hotels.push({ name, price, rating, stars, description, location: '' });
    });

    return hotels;
}

function renderStars(count) {
    const n = Math.min(5, Math.max(0, count));
    return '★'.repeat(n) + '☆'.repeat(5 - n);
}

function showError(message) {
    const c = document.getElementById('results-container');
    if (!c) return;
    c.innerHTML = `
        <div class="ai-card" style="border-color:#c0392b;">
            <div class="ai-card-head">
                <div class="ai-icon" style="border-color:#c0392b; color:#c0392b;">✕</div>
                <span class="ai-label" style="color:#c0392b;">Search Failed</span>
            </div>
            <div class="ai-content" style="color:rgba(247,242,236,0.7);">${escapeHtml(message)}</div>
            <button class="book-btn" style="margin-top:20px; width:auto; padding:12px 30px;"
                onclick="location.reload()">Try Again</button>
        </div>`;
}

function setLoading(isLoading) {
    const btn = document.getElementById('search-btn');
    if (!btn) return;
    btn.disabled = isLoading;
    btn.classList.toggle('loading', isLoading);
}

function escapeHtml(text) {
    if (text == null) return '';
    const d = document.createElement('div');
    d.textContent = String(text);
    return d.innerHTML;
}

function escapeAttr(text) {
    if (text == null) return '';
    return String(text).replace(/'/g, "\\'").replace(/"/g, '&quot;');
}