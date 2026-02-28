// API Configuration
const API_BASE_URL = 'http://localhost:8000/api/v2';

// API Client
class FinderAPI {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }

    async research(query, sessionId = null) {
        try {
            const response = await fetch(`${this.baseUrl}/research`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    session_id: sessionId
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    async getHistory(sessionId) {
        try {
            const response = await fetch(`${this.baseUrl}/history/${sessionId}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    async clearHistory(sessionId) {
        try {
            const response = await fetch(`${this.baseUrl}/history/${sessionId}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    async healthCheck() {
        try {
            const response = await fetch(`${this.baseUrl}/health`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }
}

// Export API instance
const api = new FinderAPI(API_BASE_URL);