from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

# Initialize FastAPI app
app = FastAPI(
    title="FunctioMed Chatbot API",
    description="AI Chatbot and appointment booking system",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from app.api.v1 import chat, faqs, tts
app.include_router(chat.router)
app.include_router(faqs.router)
app.include_router(tts.router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "FunctioMed Chatbot API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "functiomed-chatbot-backend"
    }

