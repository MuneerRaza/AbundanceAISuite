from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.database import Database
from pymongo.collection import Collection
from typing import Dict, List, Optional

from app.core.config import settings

# Global MongoDB client instance
client: Optional[AsyncIOMotorClient] = None

async def get_mongodb_client() -> AsyncIOMotorClient:
    """
    Get MongoDB client instance (singleton)
    """
    global client
    if client is None:
        client = AsyncIOMotorClient(settings.MONGODB_URI)
    return client

async def get_database() -> Database:
    """
    Get the database instance
    """
    client = await get_mongodb_client()
    return client[settings.MONGODB_DB_NAME]

async def get_collection(collection_name: str) -> Collection:
    """
    Get a specific MongoDB collection
    """
    db = await get_database()
    return db[collection_name]

# Collection names constants
USERS_COLLECTION = "users"
CHAT_SESSIONS_COLLECTION = "chat_sessions"
MESSAGES_COLLECTION = "messages"
DOCUMENTS_COLLECTION = "documents" 
UPDATES_COLLECTION = "updates"
TOKEN_USAGE_COLLECTION = "token_usage_logs"

# Indexes setup for better performance
async def create_indexes():
    """
    Create MongoDB indexes for better query performance
    """
    db = await get_database()
    
    # Users collection indexes
    await db[USERS_COLLECTION].create_index("email", unique=True)
    
    # Chat sessions collection indexes
    await db[CHAT_SESSIONS_COLLECTION].create_index("user_id")
    
    # Messages collection indexes
    await db[MESSAGES_COLLECTION].create_index([("chat_session_id", 1), ("timestamp", 1)])
    await db[MESSAGES_COLLECTION].create_index("user_id")
    
    # Documents collection indexes
    await db[DOCUMENTS_COLLECTION].create_index("uploader_id")
    await db[DOCUMENTS_COLLECTION].create_index("filename")
    
    # Token usage logs collection indexes
    await db[TOKEN_USAGE_COLLECTION].create_index([("user_id", 1), ("timestamp", 1)])

# Initialize MongoDB connection
async def connect_to_mongodb():
    """
    Initialize MongoDB connection and create indexes
    """
    await get_mongodb_client()
    await create_indexes()
    print("Connected to MongoDB")

# Close MongoDB connection
async def close_mongodb_connection():
    """
    Close MongoDB connection when application shuts down
    """
    global client
    if client:
        client.close()
        client = None
        print("MongoDB connection closed")
