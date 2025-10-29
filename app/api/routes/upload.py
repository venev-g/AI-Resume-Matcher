from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import List, Optional
import os
from datetime import datetime

from app.services.document_parser import document_parser
from app.services.database_service import database_service
from app.models.document import DocumentType, FileFormat, ParsedDocument, DocumentResponse
from app.core.config import settings
from app.utils.exceptions import DocumentParsingError

router = APIRouter()

@router.post("/document", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_type: DocumentType = Form(...),
    enable_ocr: bool = Form(default=True)
):
    """Upload and parse a document (resume or job description)"""
    
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Check file extension
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"File extension {file_extension} not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}"
            )
        
        # Check file size
        file_content = await file.read()
        if len(file_content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"File size exceeds maximum limit of {settings.MAX_FILE_SIZE} bytes"
            )
        
        # Parse document using Docling
        parsed_data = await document_parser.parse_document(
            file_content, 
            file.filename, 
            enable_ocr=enable_ocr
        )
        
        # Create ParsedDocument object
        file_format = FileFormat(file_extension.replace('.', ''))
        parsed_document = ParsedDocument(
            filename=file.filename,
            document_type=document_type,
            file_format=file_format,
            raw_content=parsed_data["raw_content"],
            structured_content=parsed_data["structured_content"],
            metadata=parsed_data["metadata"]
        )
        
        # Store in database
        document_id = await database_service.store_document(parsed_document)
        
        return DocumentResponse(
            id=document_id,
            filename=file.filename,
            document_type=document_type,
            status="success",
            message="Document uploaded and parsed successfully",
            parsed_at=datetime.utcnow()
        )
        
    except DocumentParsingError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@router.post("/batch", response_model=List[DocumentResponse])
async def upload_batch_documents(
    files: List[UploadFile] = File(...),
    document_types: List[DocumentType] = Form(...),
    enable_ocr: bool = Form(default=True)
):
    """Upload and parse multiple documents"""
    
    if len(files) != len(document_types):
        raise HTTPException(
            status_code=400, 
            detail="Number of files must match number of document types"
        )
    
    results = []
    
    for file, doc_type in zip(files, document_types):
        try:
            # Process each file individually
            result = await upload_document(file, doc_type, enable_ocr)
            results.append(result)
        except HTTPException as e:
            # Add error result for failed uploads
            results.append(DocumentResponse(
                id="",
                filename=file.filename or "unknown",
                document_type=doc_type,
                status="error",
                message=str(e.detail),
                parsed_at=datetime.utcnow()
            ))
    
    return results

@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(
    document_type: Optional[DocumentType] = None,
    limit: int = 50,
    offset: int = 0
):
    """List uploaded documents"""
    
    try:
        if document_type == DocumentType.RESUME:
            documents = await database_service.get_all_resumes()
        elif document_type == DocumentType.JOB_DESCRIPTION:
            documents = await database_service.get_all_job_descriptions()
        else:
            # Get all documents - this would need to be implemented in database_service
            documents = []
        
        # Apply pagination
        paginated_docs = documents[offset:offset + limit]
        
        # Convert to response format
        responses = []
        for doc in paginated_docs:
            responses.append(DocumentResponse(
                id=doc["id"],
                filename=doc["filename"],
                document_type=DocumentType(doc["document_type"]),
                status="success",
                message="Document retrieved successfully",
                parsed_at=doc["parsed_at"]
            ))
        
        return responses
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving documents: {str(e)}")

@router.get("/document/{document_id}")
async def get_document(document_id: str):
    """Get a specific document by ID"""
    
    try:
        document = await database_service.get_document_by_id(document_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return document
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving document: {str(e)}")

@router.delete("/document/{document_id}")
async def delete_document(document_id: str):
    """Delete a document"""
    
    try:
        success = await database_service.delete_document(document_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"message": "Document deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")
