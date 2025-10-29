import os
import tempfile
from typing import Dict, Any, Optional
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
import aiofiles
import logging

from app.core.config import settings
from app.utils.exceptions import DocumentParsingError

logger = logging.getLogger(__name__)

class DocumentParserService:
    def __init__(self):
        # Initialize Docling converter with OCR support
        self.converter = DocumentConverter(
            allowed_formats=[
                InputFormat.PDF,
                InputFormat.DOCX,
                InputFormat.HTML,
                InputFormat.PPTX,
                InputFormat.IMAGE
            ]
        )
        
        # Enable OCR if configured
        if settings.ENABLE_OCR:
            try:
                from docling_google_ocr import GoogleOcrDocumentConverter
                self.ocr_converter = GoogleOcrDocumentConverter()
            except ImportError:
                logger.warning("Google OCR not available, falling back to basic OCR")
                self.ocr_converter = None
    
    async def parse_document(
        self, 
        file_content: bytes, 
        filename: str,
        enable_ocr: bool = True
    ) -> Dict[str, Any]:
        """
        Parse document using Docling with enhanced OCR capabilities
        """
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}") as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                # Choose converter based on OCR requirement and availability
                if enable_ocr and self.ocr_converter and self._is_scanned_document(temp_file_path):
                    logger.info(f"Using OCR converter for {filename}")
                    result = self.ocr_converter.convert(temp_file_path)
                else:
                    logger.info(f"Using standard converter for {filename}")
                    result = self.converter.convert(temp_file_path)
                
                # Extract structured content
                parsed_content = self._extract_structured_content(result)
                
                return {
                    "raw_content": result.document.export_to_markdown(),
                    "structured_content": parsed_content,
                    "metadata": {
                        "total_pages": len(result.document.pages) if hasattr(result.document, 'pages') else 1,
                        "has_tables": self._has_tables(result.document),
                        "has_images": self._has_images(result.document),
                        "parsing_method": "ocr" if enable_ocr else "standard",
                        "file_format": self._get_file_format(filename)
                    }
                }
                
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
                
        except Exception as e:
            logger.error(f"Error parsing document {filename}: {str(e)}")
            raise DocumentParsingError(f"Failed to parse document: {str(e)}")
    
    def _is_scanned_document(self, file_path: str) -> bool:
        """
        Heuristic to determine if document might be scanned
        """
        # This is a simplified check - in practice, you might use more sophisticated methods
        file_size = os.path.getsize(file_path)
        file_extension = os.path.splitext(file_path)[1].lower()
        
        # Large PDFs might be scanned, images are definitely scanned
        if file_extension in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
            return True
        elif file_extension == '.pdf' and file_size > 1024 * 1024:  # > 1MB
            return True
        
        return False
    
    def _extract_structured_content(self, docling_result) -> Dict[str, Any]:
        """
        Extract structured information from Docling result
        """
        try:
            structured = {
                "text_content": docling_result.document.export_to_markdown(),
                "tables": [],
                "sections": [],
                "metadata": {}
            }
            
            # Extract tables if present
            if hasattr(docling_result.document, 'tables'):
                for table in docling_result.document.tables:
                    structured["tables"].append({
                        "content": table.export_to_markdown() if hasattr(table, 'export_to_markdown') else str(table),
                        "rows": getattr(table, 'num_rows', 0),
                        "cols": getattr(table, 'num_cols', 0)
                    })
            
            # Extract sections/headings
            if hasattr(docling_result.document, 'sections'):
                for section in docling_result.document.sections:
                    structured["sections"].append({
                        "title": getattr(section, 'title', ''),
                        "content": getattr(section, 'content', ''),
                        "level": getattr(section, 'level', 1)
                    })
            
            return structured
            
        except Exception as e:
            logger.warning(f"Error extracting structured content: {str(e)}")
            return {
                "text_content": docling_result.document.export_to_markdown(),
                "tables": [],
                "sections": [],
                "metadata": {"extraction_error": str(e)}
            }
    
    def _has_tables(self, document) -> bool:
        """Check if document contains tables"""
        return hasattr(document, 'tables') and len(document.tables) > 0
    
    def _has_images(self, document) -> bool:
        """Check if document contains images"""
        return hasattr(document, 'images') and len(document.images) > 0
    
    def _get_file_format(self, filename: str) -> str:
        """Get file format from filename"""
        return os.path.splitext(filename)[1].lower().replace('.', '')

# Global parser instance
document_parser = DocumentParserService()
