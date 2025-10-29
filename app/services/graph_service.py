import logging
from typing import Dict, Any, List
from app.graph.workflows import resume_matching_graph
from app.graph.state import ResumeMatchingState
from app.models.matching import MatchResult, MatchingResponse
from app.services.database_service import database_service
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class GraphService:
    def __init__(self):
        self.matching_graph = resume_matching_graph
    
    async def process_single_match(
        self,
        resume_id: str,
        jd_id: str,
        resume_content: str,
        jd_content: str
    ) -> MatchResult:
        """Process a single resume-JD match using LangGraph"""
        
        try:
            logger.info(f"Starting match processing for resume {resume_id} against JD {jd_id}")
            
            # Initialize state
            initial_state = ResumeMatchingState(
                resume_doc=resume_content,
                job_description_doc=jd_content,
                resume_id=resume_id,
                jd_id=jd_id,
                extracted_resume_skills_json="",
                validated_resume_skills_json="",
                classified_resume_skills_json="",
                extracted_jd_skills_json="",
                validated_jd_skills_json="",
                classified_jd_skills_json="",
                skill_comparison_json="",
                match_percentage=0.0,
                matched_skills=[],
                missing_skills=[],
                additional_skills=[],
                skill_gaps_json="",
                suggestions_json="",
                processing_status="initialized",
                error_message=None
            )
            
            # Run the graph
            final_state = await self.matching_graph.ainvoke(initial_state)
            
            # Check for errors
            if final_state.get("processing_status") == "error":
                raise Exception(final_state.get("error_message", "Unknown error"))
            
            # Parse results and create MatchResult
            match_result = await self._create_match_result(final_state)
            
            logger.info(f"Match processing completed. Score: {match_result.match_percentage}%")
            return match_result
            
        except Exception as e:
            logger.error(f"Error processing match: {str(e)}")
            raise
    
    async def process_batch_matching(
        self,
        jd_id: str,
        jd_content: str,
        resume_ids: List[str] = None
    ) -> MatchingResponse:
        """Process multiple resumes against a single JD"""
        
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting batch matching for JD {jd_id}")
            
            # Get resumes to process
            if resume_ids:
                resumes = await database_service.get_documents_by_ids(resume_ids)
            else:
                resumes = await database_service.get_all_resumes()
            
            high_matches = []
            close_matches = []
            low_matches = []
            
            # Process each resume
            for resume in resumes:
                try:
                    match_result = await self.process_single_match(
                        resume_id=resume["id"],
                        jd_id=jd_id,
                        resume_content=resume["raw_content"],
                        jd_content=jd_content
                    )
                    
                    # Categorize based on match percentage
                    if match_result.match_percentage >= 80.0:
                        high_matches.append(match_result)
                    elif match_result.match_percentage >= 65.0:
                        close_matches.append(match_result)
                    else:
                        low_matches.append(match_result)
                        
                    # Store result in database
                    await database_service.store_match_result(match_result)
                    
                except Exception as e:
                    logger.error(f"Error processing resume {resume['id']}: {str(e)}")
                    continue
            
            # Sort matches by percentage (descending)
            high_matches.sort(key=lambda x: x.match_percentage, reverse=True)
            close_matches.sort(key=lambda x: x.match_percentage, reverse=True)
            low_matches.sort(key=lambda x: x.match_percentage, reverse=True)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            response = MatchingResponse(
                jd_id=jd_id,
                total_resumes_processed=len(resumes),
                high_matches=high_matches,
                close_matches=close_matches,
                low_matches=low_matches,
                processing_time=processing_time
            )
            
            logger.info(f"Batch matching completed. Processed {len(resumes)} resumes in {processing_time:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"Error in batch matching: {str(e)}")
            raise
    
    async def _create_match_result(self, final_state: Dict[str, Any]) -> MatchResult:
        """Create MatchResult from final graph state"""
        
        # Parse skill comparison data
        skill_comparison_data = {}
        try:
            skill_comparison_data = json.loads(final_state.get("skill_comparison_json", "{}"))
        except json.JSONDecodeError:
            logger.warning("Failed to parse skill comparison JSON")
        
        # Extract technical and non-technical match scores
        detailed_scores = skill_comparison_data.get("detailed_scores", {})
        technical_match = detailed_scores.get("technical_skills_match", 0.0)
        non_technical_match = detailed_scores.get("professional_skills_match", 0.0)
        
        # Get recommendation
        recommendation = skill_comparison_data.get("recommendations", {}).get("hire_recommendation", "No recommendation available")
        
        # Create skill comparison object
        from app.models.skill import SkillComparison
        skill_comparison = SkillComparison(
            matched_skills=final_state.get("matched_skills", []),
            missing_skills=final_state.get("missing_skills", []),
            additional_skills=final_state.get("additional_skills", []),
            match_percentage=final_state.get("match_percentage", 0.0),
            technical_match=technical_match,
            non_technical_match=non_technical_match,
            detailed_analysis=skill_comparison_data
        )
        
        return MatchResult(
            resume_id=final_state.get("resume_id"),
            jd_id=final_state.get("jd_id"),
            match_percentage=final_state.get("match_percentage", 0.0),
            skill_comparison=skill_comparison,
            matched_skills=final_state.get("matched_skills", []),
            missing_skills=final_state.get("missing_skills", []),
            additional_skills=final_state.get("additional_skills", []),
            technical_match=technical_match,
            non_technical_match=non_technical_match,
            recommendation=recommendation,
            # processed_at=datetime.utcnow()
            processed_at=datetime.now()
        )

# Global service instance
graph_service = GraphService()
