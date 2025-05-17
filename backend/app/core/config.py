from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Abundance AI Suite"
    API_V1_STR: str = "/api/v1"
    
    # MongoDB settings
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "abundance_ai_suite")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "default_secret_key_for_dev")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    
    # LLM API Keys
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    
    # App Configuration
    DEFAULT_USER_TOKENS: int = int(os.getenv("DEFAULT_USER_TOKENS", "100"))
    
    # File Storage paths (development only)
    UPLOADED_FILES_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                                          "rag_data", "uploaded_files")
    VECTOR_INDEXES_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                                         "rag_data", "vector_indexes")
    
    # Ensure directories exist
    def ensure_directories(self):
        os.makedirs(self.UPLOADED_FILES_DIR, exist_ok=True)
        os.makedirs(self.VECTOR_INDEXES_DIR, exist_ok=True)
    
    # Admin default credentials (only for initial setup)
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@example.com")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin_secure_password")

# Create settings instance
settings = Settings()
settings.ensure_directories()
