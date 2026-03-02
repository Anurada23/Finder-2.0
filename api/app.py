import sys
from pathlib import Path

# Add parent directory to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from api.hotel_routes import router as hotel_router
from config import settings
from utils import logger
from database import snowflake_client


# Create FastAPI app
app = FastAPI(
    title="Finder AI Agent v2 - Hotel Booking System",
    description="Multi-agent AI research assistant with hotel booking capabilities",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api/v2")
app.include_router(hotel_router, prefix="/api/v2", tags=["hotels"])


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Finder AI v2 - Hotel Booking System...")
    
    try:
        # Initialize Snowflake connection
        snowflake_client.connect()
        logger.info("Snowflake connection established")
        
        # Initialize tables
        snowflake_client.initialize_tables()
        logger.info("Database tables initialized")
        
    except Exception as e:
        logger.warning(f"Startup initialization warning: {e}")
        logger.info("Continuing without Snowflake (optional feature)")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Finder AI v2...")
    
    try:
        snowflake_client.disconnect()
        logger.info("Snowflake connection closed")
    except Exception as e:
        logger.warning(f"Shutdown warning: {e}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Finder AI Agent v2 - Hotel Booking System",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "Multi-agent AI research",
            "Hotel search and booking",
            "Price comparison",
            "Context-aware memory",
            "Snowflake analytics",
            "n8n automation"
        ],
        "endpoints": {
            "docs": "/docs",
            "health": "/api/v2/health",
            "research": "/api/v2/research",
            "webhook": "/api/v2/webhook",
            "history": "/api/v2/history/{session_id}",
            "hotel_search": "/api/v2/hotels/search",
            "hotel_compare": "/api/v2/hotels/compare",
            "hotel_searches": "/api/v2/hotels/searches/{session_id}"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {settings.api_host}:{settings.api_port}")
    
    uvicorn.run(
        "api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )