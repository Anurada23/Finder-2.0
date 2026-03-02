# 🤖 Finder AI Agent v2 - Hotel Booking System

A powerful multi-agent AI research assistant with **hotel booking capabilities** built with LangChain, LangGraph, Groq, FastAPI, and Snowflake.

## 🌟 Features

- **Multi-Agent Architecture**: Specialized agents working together (Planner, Researcher, Memory, Synthesizer)
- **🏨 Hotel Booking System**: Search, compare, and book hotels using AI
- **Web Research**: DuckDuckGo search and website content extraction
- **Context-Aware Memory**: Maintains conversation history across sessions
- **Snowflake Integration**: Persistent data storage and analytics
- **FastAPI Backend**: High-performance REST API
- **Modern Frontend**: Clean, responsive UI with dedicated hotel booking interface
- **n8n Integration**: Webhook support for workflow automation

## 🏗️ Architecture

```
User → Frontend → FastAPI → LangGraph Workflow
                              ├── Memory Agent (context)
                              ├── Planner Agent (strategy)
                              ├── Researcher Agent (search & scrape)
                              └── Synthesizer Agent (final answer)
                              
Results → Snowflake Storage → n8n Follow-up Tasks
```

## 📋 Prerequisites

- Python 3.10+
- Groq API Key
- Snowflake Account (optional but recommended)
- n8n Instance (optional)

## 🚀 Installation

### 1. Clone the repository

```bash
git clone <"https://github.com/Anurada23/Finder-2.0">
cd finder-ai-v2
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env` and fill in your credentials:

```bash
# API Keys
GROQ_API_KEY=your_groq_api_key_here

# Snowflake Configuration
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_DATABASE=FINDER_AI
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_WAREHOUSE=COMPUTE_WH

# Application Settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
```

### 5. Run the application

```bash
# Start the API server
python api/app.py

# Or using uvicorn directly
uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
```

### 6. Open the frontend

Open `frontend/index.html` in your browser or serve it using:

```bash
cd frontend
python -m http.server 3000
```

Then visit: `http://localhost:3000`

## 📚 API Endpoints

### Health Check
```bash
GET /api/v2/health
```

### Research
```bash
POST /api/v2/research
Content-Type: application/json

{
  "query": "What are the latest developments in AI?",
  "session_id": "optional-session-id"
}
```

### Webhook (for n8n)
```bash
POST /api/v2/webhook
Content-Type: application/json

{
  "query": "Your research query",
  "session_id": "optional",
  "metadata": {}
}
```

### Get History
```bash
GET /api/v2/history/{session_id}
```

### Clear History
```bash
DELETE /api/v2/history/{session_id}
```

## 🔧 Configuration

### Agent Prompts

Edit agent behavior in `config/prompts.py`

### Settings

Adjust application settings in `config/settings.py`

### Memory

Configure memory limits in `.env`:
```
MAX_CONVERSATION_HISTORY=10
SESSION_TIMEOUT_MINUTES=30
```

## 🗄️ Snowflake Setup

### 1. Create Database

```sql
CREATE DATABASE FINDER_AI;
USE DATABASE FINDER_AI;
CREATE SCHEMA PUBLIC;
```

### 2. Tables are auto-created on startup

The application automatically creates:
- `research_sessions` - Main research data
- `conversation_history` - Chat history
- `agent_traces` - Agent execution logs

## 🔗 n8n Integration

### Setup Webhook in n8n

1. Create new workflow in n8n
2. Add "Webhook" node
3. Set Method: POST
4. Set Path: `/finder-webhook`
5. Add "HTTP Request" node
6. Configure:
   - Method: POST
   - URL: `http://your-api:8000/api/v2/webhook`
   - Body: JSON
   ```json
   {
     "query": "{{$json.query}}",
     "session_id": "{{$json.session_id}}"
   }
   ```

### Follow-up Tasks Examples

After receiving response, you can:

1. **Save to Google Sheets**
   - Add Google Sheets node
   - Map response data to columns

2. **Send Email Summary**
   - Add Gmail/SendGrid node
   - Include research findings

3. **Trigger Additional Research**
   - Add conditional logic
   - Loop back if incomplete

4. **Store in Database**
   - Add database node (MySQL, Postgres)
   - Save structured data

## 🧪 Testing

```bash
# Run tests
pytest tests/

# Test specific module
pytest tests/test_agents.py

# With coverage
pytest --cov=. tests/
```

## 📁 Project Structure

```
finder-ai-v2/
├── agents/           # AI agents
├── api/              # FastAPI application
├── config/           # Configuration
├── database/         # Snowflake integration
├── frontend/         # Web interface
├── memory/           # Context management
├── tools/            # Agent tools
├── utils/            # Utilities
├── workflows/        # LangGraph workflows
├── .env              # Environment variables
└── requirements.txt  # Dependencies
```

## 🐛 Troubleshooting

### API Not Connecting
- Check if server is running: `curl http://localhost:8000/api/v2/health`
- Verify GROQ_API_KEY is set
- Check firewall settings

### Snowflake Connection Failed
- Verify credentials in `.env`
- Check network access to Snowflake
- Application will work without Snowflake (memory-only mode)

### Frontend Not Loading
- Check CORS settings in `api/app.py`
- Verify API URL in `frontend/js/api.js`
- Check browser console for errors

## 🔐 Security Notes

- Never commit `.env` file
- Use environment variables in production
- Implement rate limiting for production
- Add authentication for public deployment

## 📈 Performance Tips

- Adjust `MAX_CONVERSATION_HISTORY` based on needs
- Use Snowflake for long-term storage
- Implement caching for frequent queries
- Monitor API token usage

## 🛣️ Roadmap

- [ ] Add vector store for semantic search
- [ ] Implement streaming responses
- [ ] Add user authentication
- [ ] Create analytics dashboard
- [ ] Support multiple LLM providers
- [ ] Add PDF/document upload
- [ ] Implement RAG pipeline

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Open Pull Request

## 📄 License

MIT License - See LICENSE file

## 👥 Authors

Anuradha Senaratne

## 🙏 Acknowledgments

- LangChain & LangGraph
- Groq
- FastAPI
- Snowflake
- n8n

---