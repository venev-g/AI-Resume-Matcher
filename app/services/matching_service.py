import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.services.graph_service import graph_service
from app.services.database_service import database_service
from app.models.matching import MatchResult, MatchingResponse
from app.core.config import settings

logger = logging.getLogger(__name__)

class MatchingService:
    """High-level service for resume-JD matching operations"""
    
    def __init__(self):
        self.similarity_threshold = settings.SIMILARITY_THRESHOLD
        self.close_match_threshold = settings.CLOSE_MATCH_THRESHOLD
    
    async def find_matching_resumes(
        self,
        jd_id: str,
        min_score: float = None,
        limit: int = 100
    ) -> List[MatchResult]:
        """Find resumes that match a job description above specified threshold"""
        
        min_score = min_score or (self.similarity_threshold * 100)  # Convert to percentage
        
        try:
            logger.info(f"Finding matching resumes for JD {jd_id} with min score {min_score}%")
            
            # Get job description
            jd_doc = await database_service.get_document_by_id(jd_id)
            if not jd_doc:
                raise ValueError(f"Job description {jd_id} not found")
            
            # Get all resumes
            resumes = await database_service.get_all_resumes()
            
            matching_resumes = []
            processed_count = 0
            
            for resume in resumes:
                if processed_count >= limit:
                    break
                
                try:
                    # Check if match already exists
                    existing_match = await database_service.get_match_result(
                        resume["id"], jd_id
                    )
                    
                    if existing_match:
                        # Use existing match if above threshold
                        if existing_match.get("match_percentage", 0) >= min_score:
                            # Convert dict to MatchResult (simplified)
                            matching_resumes.append(existing_match)
                    else:
                        # Process new match
                        match_result = await graph_service.process_single_match(
                            resume_id=resume["id"],
                            jd_id=jd_id,
                            resume_content=resume["raw_content"],
                            jd_content=jd_doc["raw_content"]
                        )
                        
                        if match_result.match_percentage >= min_score:
                            matching_resumes.append(match_result)
                    
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing resume {resume['id']}: {e}")
                    continue
            
            # Sort by match percentage
            matching_resumes.sort(
                key=lambda x: x.match_percentage if hasattr(x, 'match_percentage') else x.get('match_percentage', 0),
                reverse=True
            )
            
            logger.info(f"Found {len(matching_resumes)} matching resumes")
            return matching_resumes
            
        except Exception as e:
            logger.error(f"Error finding matching resumes: {e}")
            raise
    
    async def get_close_matches_for_improvement(
        self,
        jd_id: str
    ) -> List[Dict[str, Any]]:
        """Get resumes with close matches (65-79%) that could be improved"""
        
        try:
            logger.info(f"Finding close matches for JD {jd_id}")
            
            # Get all matches for this JD
            all_matches = await database_service.get_match_results_by_jd(jd_id)
            
            # Filter close matches
            close_matches = []
            for match in all_matches:
                match_percentage = match.get("match_percentage", 0)
                if (self.close_match_threshold * 100) <= match_percentage < (self.similarity_threshold * 100):
                    close_matches.append(match)
            
            # Sort by match percentage (highest first)
            close_matches.sort(key=lambda x: x.get("match_percentage", 0), reverse=True)
            
            logger.info(f"Found {len(close_matches)} close matches")
            return close_matches
            
        except Exception as e:
            logger.error(f"Error finding close matches: {e}")
            raise
    
    async def bulk_match_update(
        self,
        jd_id: str,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Update matches for all resumes against a specific JD"""
        
        try:
            logger.info(f"Starting bulk match update for JD {jd_id}")
            
            start_time = datetime.utcnow()
            # start_time = datetime.now()
            
            # Get job description
            jd_doc = await database_service.get_document_by_id(jd_id)
            if not jd_doc:
                raise ValueError(f"Job description {jd_id} not found")
            
            # Get all resumes
            resumes = await database_service.get_all_resumes()
            
            stats = {
                "total_resumes": len(resumes),
                "processed": 0,
                "updated": 0,
                "skipped": 0,
                "errors": 0,
                "high_matches": 0,
                "close_matches": 0,
                "low_matches": 0
            }
            
            for resume in resumes:
                try:
                    # Check if match exists and if refresh is needed
                    existing_match = await database_service.get_match_result(
                        resume["id"], jd_id
                    )
                    
                    if existing_match and not force_refresh:
                        stats["skipped"] += 1
                        continue
                    
                    # Process match
                    match_result = await graph_service.process_single_match(
                        resume_id=resume["id"],
                        jd_id=jd_id,
                        resume_content=resume["raw_content"],
                        jd_content=jd_doc["raw_content"]
                    )
                    
                    # Update statistics
                    if match_result.match_percentage >= 80:
                        stats["high_matches"] += 1
                    elif match_result.match_percentage >= 65:
                        stats["close_matches"] += 1
                    else:
                        stats["low_matches"] += 1
                    
                    stats["updated"] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing resume {resume['id']}: {e}")
                    stats["errors"] += 1
                
                stats["processed"] += 1
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"Bulk update completed in {processing_time:.2f}s")
            
            return {
                "jd_id": jd_id,
                "processing_time": processing_time,
                "statistics": stats,
                "completed_at": datetime.utcnow().isoformat()
              # "completed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in bulk match update: {e}")
            raise

# Global service instance
matching_service = MatchingService()
