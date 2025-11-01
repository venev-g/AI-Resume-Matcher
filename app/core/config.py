import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Resume-JD Matching System"
    
    # Server Configuration
    PORT: int = Field(default=8000, description="Server port")
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001"
    ]
    
    # MongoDB Atlas Configuration
    MONGODB_URL: str = Field(default="", description="MongoDB connection URL")
    DATABASE_NAME: str = Field(default="resume_matcher", description="Database name")
    
    # MongoDB Atlas Components (alternative to full connection string)
    MONGODB_USERNAME: Optional[str] = Field(default=None, description="MongoDB username")
    MONGODB_PASSWORD: Optional[str] = Field(default=None, description="MongoDB password")
    MONGODB_CLUSTER_URL: Optional[str] = Field(default=None, description="MongoDB cluster URL")
    
    # LLM Configuration
    GEMINI_API_KEY: str = Field(default="", description="Gemini API key")
    OPENROUTER_API_KEY: str = Field(default="", description="OpenRouter API key")
    DEFAULT_LLM_PROVIDER: str = Field(default="", description="Default LLM provider")
    
    # Model Configurations
    GEMINI_MODEL: str = Field(default="gemini-2.5-flash", description="Gemini model name")
    OPENROUTER_MODEL: str = Field(default="openai/gpt-oss-20b:free", description="OpenRouter model name")
    
    # File Upload
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024, description="Maximum file size in bytes")  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt"]
    UPLOAD_DIR: str = Field(default="uploads", description="Upload directory")
    
    # Matching Configuration
    SIMILARITY_THRESHOLD: float = Field(default=0.80, description="Similarity threshold for matching")
    CLOSE_MATCH_THRESHOLD: float = Field(default=0.65, description="Close match threshold")
    
    # OCR Configuration
    ENABLE_OCR: bool = Field(default=True, description="Enable OCR processing")
    OCR_ENGINE: str = Field(default="easyocr", description="OCR engine to use")
    
    # Database Connection Options
    DB_CONNECTION_TIMEOUT: int = Field(default=10000, description="Database connection timeout in ms")
    DB_SERVER_SELECTION_TIMEOUT: int = Field(default=5000, description="Database server selection timeout in ms")
    DB_MAX_POOL_SIZE: int = Field(default=10, description="Maximum database connection pool size")
    DB_MIN_POOL_SIZE: int = Field(default=1, description="Minimum database connection pool size")
    
    # LLM Configuration
    LLM_MAX_RETRIES: int = Field(default=3, description="Maximum LLM API retries")
    LLM_DEFAULT_TEMPERATURE: float = Field(default=0.7, description="Default LLM temperature")
    LLM_DEFAULT_MAX_TOKENS: int = Field(default=4000, description="Default maximum tokens")
    LLM_MAX_CONCURRENT_REQUESTS: int = Field(default=5, description="Maximum concurrent LLM requests")
    
    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = False
        # Allow extra fields from environment
        extra = "ignore"

settings = Settings()
