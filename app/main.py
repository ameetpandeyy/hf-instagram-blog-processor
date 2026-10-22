from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routers import webhooks, health
from app.config import get_settings
import logging

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Instagram Blog Processor",
    description="AI service for processing Instagram posts into blog articles",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="", tags=["health"])
app.include_router(webhooks.router, prefix="/webhook", tags=["webhooks"])

@app.on_event("startup")
async def startup_event():
    logger.info("Instagram Blog Processor starting up...")
    logger.info(f"Gemini Model: {settings.gemini_model}")
    logger.info(f"Callback URL: {settings.callback_url}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Instagram Blog Processor shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
