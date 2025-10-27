"""Pinecone vector database service for semantic search."""

import logging
import os
from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec

logger = logging.getLogger(__name__)


class PineconeService:
    """Service for managing Pinecone vector database operations."""

    def __init__(self):
        """Initialize Pinecone client and configuration."""
        self.api_key = os.getenv("PINECONE_API_KEY")
        self.environment = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "resume-jd-matcher")
        self.dimension = 768
        self.metric = "cosine"
        
        if not self.api_key:
            raise ValueError("PINECONE_API_KEY environment variable not set")
        
        self.client = Pinecone(api_key=self.api_key)
        self.index = None
        self._initialize_index()

    def _initialize_index(self) -> None:
        """Initialize or connect to existing Pinecone index."""
        try:
            existing_indexes = [index.name for index in self.client.list_indexes()]
            
            if self.index_name not in existing_indexes:
                logger.info(f"Creating new Pinecone index: {self.index_name}")
                self.client.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric=self.metric,
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=self.environment
                    )
                )
                logger.info(f"Successfully created index: {self.index_name}")
            else:
                logger.info(f"Connecting to existing index: {self.index_name}")
            
            self.index = self.client.Index(self.index_name)
            
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone index: {e}")
            raise

    async def upsert_resume(
        self,
        resume_id: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Upsert a resume embedding to Pinecone.
        
        Args:
            resume_id: Unique identifier for the resume
            embedding: 768-dimensional embedding vector
            metadata: Resume metadata (candidate name, skills, etc.)
            
        Returns:
            True if upsert successful, False otherwise
            
        Raises:
            ValueError: If embedding dimension is incorrect
        """
        try:
            if len(embedding) != self.dimension:
                raise ValueError(
                    f"Embedding dimension mismatch. Expected {self.dimension}, got {len(embedding)}"
                )
            
            self.index.upsert(
                vectors=[{
                    "id": resume_id,
                    "values": embedding,
                    "metadata": metadata
                }]
            )
            
            logger.info(f"Successfully upserted resume: {resume_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upsert resume {resume_id}: {e}")
            return False

    async def upsert_batch(
        self,
        vectors: List[Dict[str, Any]]
    ) -> bool:
        """
        Batch upsert multiple resume embeddings.
        
        Args:
            vectors: List of vector dictionaries with id, values, and metadata
            
        Returns:
            True if batch upsert successful, False otherwise
        """
        try:
            batch_size = 100
            
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(vectors=batch)
                logger.info(f"Upserted batch {i // batch_size + 1} ({len(batch)} vectors)")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to upsert batch: {e}")
            return False

    async def query_similar(
        self,
        embedding: List[float],
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query for similar resumes based on embedding.
        
        Args:
            embedding: Query embedding vector
            top_k: Number of top matches to return
            filter_dict: Optional metadata filter
            
        Returns:
            List of matching results with scores and metadata
            
        Raises:
            ValueError: If embedding dimension is incorrect
        """
        try:
            if len(embedding) != self.dimension:
                raise ValueError(
                    f"Embedding dimension mismatch. Expected {self.dimension}, got {len(embedding)}"
                )
            
            results = self.index.query(
                vector=embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict
            )
            
            matches = []
            for match in results.matches:
                matches.append({
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata
                })
            
            logger.info(f"Found {len(matches)} similar resumes")
            return matches
            
        except Exception as e:
            logger.error(f"Failed to query similar resumes: {e}")
            return []

    async def delete_resume(self, resume_id: str) -> bool:
        """
        Delete a resume from the index.
        
        Args:
            resume_id: Unique identifier of the resume to delete
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            self.index.delete(ids=[resume_id])
            logger.info(f"Successfully deleted resume: {resume_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete resume {resume_id}: {e}")
            return False

    async def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the Pinecone index.
        
        Returns:
            Dictionary containing index statistics
        """
        try:
            stats = self.index.describe_index_stats()
            return {
                "total_vectors": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness
            }
            
        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            return {}
