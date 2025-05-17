from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from contextlib import asynccontextmanager
from datetime import datetime # Add this import
import logging

from app.core.config import settings
from app.db.mongodb_utils import connect_to_mongodb, close_mongodb_connection, get_collection, USERS_COLLECTION
from app.apis.endpoints import auth, users, admin, chat, upload
from app.core.security import get_password_hash
from app.db.models import UserRole

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Lifespan event handlers for database connection
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup: Connecting to MongoDB...")
    await connect_to_mongodb()
    
    # Create initial admin user if not exists
    logger.info("Checking for initial admin user...")
    users_collection = await get_collection(USERS_COLLECTION)
    admin_user = await users_collection.find_one({"email": settings.ADMIN_EMAIL})
    if not admin_user:
        logger.info(f"Admin user not found. Creating admin: {settings.ADMIN_EMAIL}")
        hashed_password = get_password_hash(settings.ADMIN_PASSWORD) # Using plain text for dev
        admin_data = {
            "email": settings.ADMIN_EMAIL,
            "password_hash": hashed_password,
            "full_name": "Default Admin",
            "role": UserRole.ADMIN,
            "tokens_remaining": settings.DEFAULT_USER_TOKENS * 100, # Generous tokens for admin
            "active": True,
            "created_at": datetime.utcnow()
        }
        await users_collection.insert_one(admin_data)
        logger.info(f"Admin user {settings.ADMIN_EMAIL} created successfully.")
    else:
        logger.info(f"Admin user {settings.ADMIN_EMAIL} already exists.")
        
    yield
    logger.info("Application shutdown: Closing MongoDB connection...")
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
    return {"message": f"Welcome to {settings.PROJECT_NAME} API"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
