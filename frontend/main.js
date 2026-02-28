// Session Management
let currentSessionId = null;

// DOM Elements
const chatContainer = document.getElementById('chat-container');
const queryInput = document.getElementById('query-input');
const sendBtn = document.getElementById('send-btn');
const clearBtn = document.getElementById('clear-btn');
const sessionIdDisplay = document.getElementById('session-id');
const sendText = document.getElementById('send-text');
const loadingSpinner = document.getElementById('loading-spinner');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeSession();
    setupEventListeners();
    checkAPIHealth();
});

// Initialize session
function initializeSession() {
    currentSessionId = generateSessionId();
    updateSessionDisplay();
}

// Generate unique session ID
function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// Update session display
function updateSessionDisplay() {
    sessionIdDisplay.textContent = `Session: ${currentSessionId.substr(0, 20)}...`;
}

// Setup event listeners
function setupEventListeners() {
    // Send button
    sendBtn.addEventListener('click', handleSend);
    
    // Enter key (without Shift)
    queryInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    });
    
    // Auto-resize textarea
    queryInput.addEventListener('input', () => {
        queryInput.style.height = 'auto';
        queryInput.style.height = queryInput.scrollHeight + 'px';
    });
    
    // Clear button
    clearBtn.addEventListener('click', handleClear);
}

// Handle send message
async function handleSend() {
    const query = queryInput.value.trim();
    
    if (!query) {
        return;
    }
    
    // Clear input
    queryInput.value = '';
    queryInput.style.height = 'auto';
    
    // Remove welcome message if present
    const welcomeMsg = document.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }
    
    // Add user message to chat
    addMessage('user', query);
    
    // Show loading state
    setLoading(true);
    
    try {
        // Call API
        const response = await api.research(query, currentSessionId);
        
        // Add assistant response
        addMessage('assistant', response.response);
        
        // Update session ID if new
        if (response.session_id && response.session_id !== currentSessionId) {
            currentSessionId = response.session_id;
            updateSessionDisplay();
        }
        
    } catch (error) {
        console.error('Error:', error);
        addMessage('assistant', `Sorry, I encountered an error: ${error.message}. Please try again.`);
    } finally {
        setLoading(false);
    }
}

// Add message to chat
function addMessage(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const avatar = role === 'user' ? '👤' : '🤖';
    const roleName = role === 'user' ? 'You' : 'Finder AI';
    
    messageDiv.innerHTML = `
        <div class="message-header">
            <div class="message-avatar">${avatar}</div>
            <span class="message-role">${roleName}</span>
        </div>
        <div class="message-content">${escapeHtml(content)}</div>
    `;
    
    chatContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Set loading state
function setLoading(isLoading) {
    if (isLoading) {
        sendBtn.disabled = true;
        sendText.classList.add('hidden');
        loadingSpinner.classList.remove('hidden');
    } else {
        sendBtn.disabled = false;
        sendText.classList.remove('hidden');
        loadingSpinner.classList.add('hidden');
    }
}

// Handle clear chat
async function handleClear() {
    if (!confirm('Are you sure you want to clear the chat history?')) {
        return;
    }
    
    try {
        await api.clearHistory(currentSessionId);
        
        // Clear chat container
        chatContainer.innerHTML = `
            <div class="welcome-message">
                <h2>👋 Welcome to Finder AI</h2>
                <p>Ask me anything! I can search the web, visit websites, and provide comprehensive answers.</p>
                <div class="features">
                    <div class="feature">
                        <span class="icon">🔍</span>
                        <span>Web Search</span>
                    </div>
                    <div class="feature">
                        <span class="icon">🌐</span>
                        <span>Website Analysis</span>
                    </div>
                    <div class="feature">
                        <span class="icon">🧠</span>
                        <span>Context Memory</span>
                    </div>
                    <div class="feature">
                        <span class="icon">📊</span>
                        <span>Data Storage</span>
                    </div>
                </div>
            </div>
        `;
        
        // Generate new session
        initializeSession();
        
    } catch (error) {
        console.error('Error clearing history:', error);
        alert('Failed to clear history. Please try again.');
    }
}

// Check API health
async function checkAPIHealth() {
    try {
        const health = await api.healthCheck();
        console.log('API Health:', health);
    } catch (error) {
        console.error('API is not responding:', error);
        addMessage('assistant', '⚠️ Warning: API server is not responding. Please make sure the backend is running on http://localhost:8000');
    }
}

// Utility: Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Focus input on load
queryInput.focus();