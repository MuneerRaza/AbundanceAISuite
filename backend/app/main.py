from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer

import logging
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.mongodb_utils import connect_to_mongodb, close_mongodb_connection
from app.apis.endpoints import auth, users, admin, chat, upload

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Lifespan event handlers for database connection
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect to MongoDB on startup
    await connect_to_mongodb()
    yield
    # Close MongoDB connection on shutdown
    await close_mongodb_connection()

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for Abundance AI Suite - An AI-powered assistant and content generation platform.",
    version="0.1.0",
    lifespan=lifespan,
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers from endpoint modules
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["Authentication"],
)

app.include_router(
    users.router,
    prefix=f"{settings.API_V1_STR}/users",
    tags=["Users"],
)

app.include_router(
    admin.router,
    prefix=f"{settings.API_V1_STR}/admin",
    tags=["Admin"],
)

app.include_router(
    chat.router,
    prefix=f"{settings.API_V1_STR}/chat",
    tags=["Chat"],
)

app.include_router(
    upload.router,
    prefix=f"{settings.API_V1_STR}/upload",
    tags=["Upload"],
)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to Abundance AI Suite API",
        "documentation": "/docs",
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
