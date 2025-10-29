import os
import mimetypes
from typing import List, Tuple, Optional
from pathlib import Path

from app.core.config import settings

class FileHandler:
    """Utility class for file operations"""
    
    @staticmethod
    def validate_file_extension(filename: str) -> bool:
        """Validate if file extension is allowed"""
        if not filename:
            return False
        
        file_extension = os.path.splitext(filename)[1].lower()
        return file_extension in settings.ALLOWED_EXTENSIONS
    
    @staticmethod
    def get_file_format(filename: str) -> Optional[str]:
        """Get file format from filename"""
        if not filename:
            return None
        
        file_extension = os.path.splitext(filename)[1].lower()
        return file_extension.replace('.', '')
    
    @staticmethod
    def get_mime_type(filename: str) -> Optional[str]:
        """Get MIME type for file"""
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type
    
    @staticmethod
    def validate_file_size(file_size: int) -> bool:
        """Validate if file size is within limits"""
        return file_size <= settings.MAX_FILE_SIZE
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent security issues"""
        # Remove path separators and other dangerous characters
        filename = os.path.basename(filename)
        # Remove any non-alphanumeric characters except dots, hyphens, and underscores
        sanitized = ''.join(c for c in filename if c.isalnum() or c in '._-')
        return sanitized
    
    @staticmethod
    def ensure_upload_directory() -> None:
        """Ensure upload directory exists"""
        upload_path = Path(settings.UPLOAD_DIR)
        upload_path.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def get_supported_formats() -> List[str]:
        """Get list of supported file formats"""
        return settings.ALLOWED_EXTENSIONS
    