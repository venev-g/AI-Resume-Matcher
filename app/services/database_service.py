import os
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import uuid
import logging

from app.core.config import settings
from app.models.document import ParsedDocument, DocumentType
from app.models.matching import MatchResult

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        self.client = None
        self.database = None
        self.documents_collection = None
        self.matches_collection = None
    
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(settings.MONGODB_URL)
            self.database = self.client[settings.DATABASE_NAME]
            self.documents_collection = self.database.documents
            self.matches_collection = self.database.matches
            
            # Create indexes
            await self._create_indexes()
            
            logger.info("Connected to MongoDB successfully")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    async def _create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Documents collection indexes
            await self.documents_collection.create_index("document_type")
            await self.documents_collection.create_index("filename")
            await self.documents_collection.create_index("parsed_at")
            
            # Matches collection indexes
            await self.matches_collection.create_index([("jd_id", 1), ("resume_id", 1)])
            await self.matches_collection.create_index("match_percentage")
            await self.matches_collection.create_index("processed_at")
            
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")
    
    async def store_document(self, document: ParsedDocument) -> str:
        """Store a parsed document in the database"""
        try:
            document_dict = document.dict()
            if not document_dict.get("id"):
                document_dict["id"] = str(uuid.uuid4())
            
            await self.documents_collection.insert_one(document_dict)
            
            logger.info(f"Document {document.filename} stored with ID: {document_dict['id']}")
            return document_dict["id"]
            
        except Exception as e:
            logger.error(f"Error storing document: {e}")
            raise
    
    async def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a document by ID"""
        try:
            document = await self.documents_collection.find_one({"id": document_id})
            return document
        except Exception as e:
            logger.error(f"Error retrieving document {document_id}: {e}")
            raise
    
    async def get_documents_by_ids(self, document_ids: List[str]) -> List[Dict[str, Any]]:
        """Retrieve multiple documents by IDs"""
        try:
            cursor = self.documents_collection.find({"id": {"$in": document_ids}})
            documents = await cursor.to_list(length=None)
            return documents
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            raise
    
    async def get_all_resumes(self) -> List[Dict[str, Any]]:
        """Get all resume documents"""
        try:
            cursor = self.documents_collection.find({"document_type": DocumentType.RESUME})
            resumes = await cursor.to_list(length=None)
            return resumes
        except Exception as e:
            logger.error(f"Error retrieving resumes: {e}")
            raise
    
    async def get_all_job_descriptions(self) -> List[Dict[str, Any]]:
        """Get all job description documents"""
        try:
            cursor = self.documents_collection.find({"document_type": DocumentType.JOB_DESCRIPTION})
            jds = await cursor.to_list(length=None)
            return jds
        except Exception as e:
            logger.error(f"Error retrieving job descriptions: {e}")
            raise
    
    async def store_match_result(self, match_result: MatchResult) -> str:
        """Store a match result in the database"""
        try:
            match_dict = match_result.dict()
            # match_dict = match_result.model_dump()
            match_dict["id"] = str(uuid.uuid4())
            
            await self.matches_collection.insert_one(match_dict)
            
            logger.info(f"Match result stored with ID: {match_dict['id']}")
            return match_dict["id"]
            
        except Exception as e:
            logger.error(f"Error storing match result: {e}")
            raise
    
    async def get_match_results_by_jd(self, jd_id: str) -> List[Dict[str, Any]]:
        """Get all match results for a specific job description"""
        try:
            cursor = self.matches_collection.find({"jd_id": jd_id})
            matches = await cursor.to_list(length=None)
            return matches
        except Exception as e:
            logger.error(f"Error retrieving match results for JD {jd_id}: {e}")
            raise
    
    async def get_match_result(self, resume_id: str, jd_id: str) -> Optional[Dict[str, Any]]:
        """Get specific match result between resume and JD"""
        try:
            match = await self.matches_collection.find_one({
                "resume_id": resume_id,
                "jd_id": jd_id
            })
            return match
        except Exception as e:
            logger.error(f"Error retrieving match result: {e}")
            raise
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete a document from the database"""
        try:
            result = await self.documents_collection.delete_one({"id": document_id})
            if result.deleted_count > 0:
                logger.info(f"Document {document_id} deleted successfully")
                return True
            else:
                logger.warning(f"Document {document_id} not found for deletion")
                return False
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            raise
    
    async def search_documents(
        self, 
        query: str, 
        document_type: Optional[DocumentType] = None
    ) -> List[Dict[str, Any]]:
        """Search documents by text content"""
        try:
            search_filter = {"$text": {"$search": query}}
            if document_type:
                search_filter["document_type"] = document_type
            
            cursor = self.documents_collection.find(search_filter)
            documents = await cursor.to_list(length=None)
            return documents
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            raise

# Global database service instance
database_service = DatabaseService()
