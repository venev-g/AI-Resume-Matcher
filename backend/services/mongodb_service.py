"""MongoDB service for storing match results and metadata."""

import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure

logger = logging.getLogger(__name__)


class MongoDBService:
    """Service for managing MongoDB operations."""

    def __init__(self):
        """Initialize MongoDB async client."""
        self.uri = os.getenv("MONGODB_URI")
        self.database_name = os.getenv("MONGODB_DATABASE", "resume_system")
        
        if not self.uri:
            raise ValueError("MONGODB_URI environment variable not set")
        
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.match_results_collection = None
        self.evaluations_collection = None

    async def connect(self) -> None:
        """Establish connection to MongoDB and initialize collections."""
        try:
            self.client = AsyncIOMotorClient(self.uri)
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
            
            self.db = self.client[self.database_name]
            self.match_results_collection = self.db.match_results
            self.evaluations_collection = self.db.evaluations
            
            # Create indexes
            await self._create_indexes()
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during MongoDB connection: {e}")
            raise

    async def _create_indexes(self) -> None:
        """Create indexes on frequently queried fields."""
        try:
            # Index on timestamp for chronological queries
            await self.match_results_collection.create_index("timestamp")
            
            # Index on jd_text for duplicate detection
            await self.match_results_collection.create_index("jd_text")
            
            # Index on match_score for filtering
            await self.match_results_collection.create_index("match_score")
            
            logger.info("Successfully created MongoDB indexes")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")

    async def store_match_result(
        self,
        jd_text: str,
        jd_data: Dict[str, Any],
        matches: List[Dict[str, Any]]
    ) -> Optional[str]:
        """
        Store match results in MongoDB.
        
        Args:
            jd_text: Original job description text
            jd_data: Extracted job description data
            matches: List of resume match results
            
        Returns:
            Document ID if successful, None otherwise
        """
        try:
            document = {
                "jd_text": jd_text,
                "jd_data": jd_data,
                "matches": matches,
                "total_resumes": len(matches),
                "high_matches": sum(1 for m in matches if m.get("match_score", 0) >= 80),
                "potential_matches": sum(
                    1 for m in matches if 65 <= m.get("match_score", 0) < 80
                ),
                "timestamp": datetime.utcnow(),
                "status": "completed"
            }
            
            result = await self.match_results_collection.insert_one(document)
            logger.info(f"Stored match result with ID: {result.inserted_id}")
            
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to store match result: {e}")
            return None

    async def get_match_history(
        self,
        limit: int = 10,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve match history from database.
        
        Args:
            limit: Maximum number of records to return
            skip: Number of records to skip for pagination
            
        Returns:
            List of match result documents
        """
        try:
            cursor = self.match_results_collection.find().sort(
                "timestamp", -1
            ).skip(skip).limit(limit)
            
            results = await cursor.to_list(length=limit)
            
            # Convert ObjectId to string for JSON serialization
            for result in results:
                result["_id"] = str(result["_id"])
            
            logger.info(f"Retrieved {len(results)} match history records")
            return results
            
        except Exception as e:
            logger.error(f"Failed to get match history: {e}")
            return []

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get aggregate statistics from all match results.
        
        Returns:
            Dictionary containing statistics
        """
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total_evaluations": {"$sum": 1},
                        "total_resumes_processed": {"$sum": "$total_resumes"},
                        "total_high_matches": {"$sum": "$high_matches"},
                        "total_potential_matches": {"$sum": "$potential_matches"},
                        "avg_match_score": {"$avg": {"$avg": "$matches.match_score"}}
                    }
                }
            ]
            
            cursor = self.match_results_collection.aggregate(pipeline)
            results = await cursor.to_list(length=1)
            
            if results:
                stats = results[0]
                stats.pop("_id", None)
                logger.info("Successfully retrieved statistics")
                return stats
            else:
                return {
                    "total_evaluations": 0,
                    "total_resumes_processed": 0,
                    "total_high_matches": 0,
                    "total_potential_matches": 0,
                    "avg_match_score": 0.0
                }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}

    async def store_evaluation(
        self,
        resume_id: str,
        evaluation_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Store individual resume evaluation.
        
        Args:
            resume_id: Unique identifier for the resume
            evaluation_data: Evaluation results and metadata
            
        Returns:
            Document ID if successful, None otherwise
        """
        try:
            document = {
                "resume_id": resume_id,
                **evaluation_data,
                "timestamp": datetime.utcnow()
            }
            
            result = await self.evaluations_collection.insert_one(document)
            logger.info(f"Stored evaluation for resume: {resume_id}")
            
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to store evaluation: {e}")
            return None

    async def get_resume_evaluations(
        self,
        resume_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all evaluations for a specific resume.
        
        Args:
            resume_id: Unique identifier for the resume
            
        Returns:
            List of evaluation documents
        """
        try:
            cursor = self.evaluations_collection.find(
                {"resume_id": resume_id}
            ).sort("timestamp", -1)
            
            results = await cursor.to_list(length=None)
            
            for result in results:
                result["_id"] = str(result["_id"])
            
            logger.info(f"Retrieved {len(results)} evaluations for resume: {resume_id}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to get resume evaluations: {e}")
            return []

    async def close(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
