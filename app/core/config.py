import os
from typing import List, Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Resume-JD Matching System"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001"
    ]
    
    # MongoDB Atlas Configuration
    MONGODB_URL: str = os.getenv("MONGODB_URL", "")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "resume_matcher")
    
    # MongoDB Atlas Components (alternative to full connection string)
    MONGODB_USERNAME: Optional[str] = os.getenv("MONGODB_USERNAME")
    MONGODB_PASSWORD: Optional[str] = os.getenv("MONGODB_PASSWORD")
    MONGODB_CLUSTER_URL: Optional[str] = os.getenv("MONGODB_CLUSTER_URL")
    
    # LLM Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    DEFAULT_LLM_PROVIDER: str = os.getenv("DEFAULT_LLM_PROVIDER", "gemini")
    
    # File Upload
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt"]
    UPLOAD_DIR: str = "uploads"
    
    # Matching Configuration
    SIMILARITY_THRESHOLD: float = 0.80
    CLOSE_MATCH_THRESHOLD: float = 0.65
    
    # OCR Configuration
    ENABLE_OCR: bool = True
    OCR_ENGINE: str = "easyocr"
    
    # Database Connection Options
    DB_CONNECTION_TIMEOUT: int = 10000  # 10 seconds
    DB_SERVER_SELECTION_TIMEOUT: int = 5000  # 5 seconds
    DB_MAX_POOL_SIZE: int = 10
    DB_MIN_POOL_SIZE: int = 1
    
    class Config:
        env_file = ".env"

settings = Settings()
