"""LangGraph workflow orchestrator for resume matching system."""

import logging
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END

from agents.jd_extractor import JDExtractorAgent
from agents.resume_analyzer import ResumeAnalyzerAgent
from agents.embedding_agent import EmbeddingAgent
from agents.match_evaluator import MatchEvaluatorAgent
from agents.skill_recommender import SkillRecommenderAgent
from services.mongodb_service import MongoDBService
from services.pinecone_service import PineconeService

logger = logging.getLogger(__name__)


class GraphState(TypedDict):
    """State definition for LangGraph workflow."""
    
    jd_text: str
    resume_files: List[str]
    jd_data: Optional[Dict[str, Any]]
    resume_data: List[Dict[str, Any]]
    jd_embedding: Optional[List[float]]
    resume_embeddings: List[Dict[str, Any]]
    match_results: List[Dict[str, Any]]
    final_output: Optional[Dict[str, Any]]
    error: Optional[str]


class GraphExecutor:
    """Orchestrates the multi-agent resume matching workflow using LangGraph."""

    def __init__(self):
        """Initialize all agents and services."""
        logger.info("Initializing GraphExecutor with all agents and services")
        
        # Initialize agents
        self.jd_extractor = JDExtractorAgent()
        self.resume_analyzer = ResumeAnalyzerAgent()
        self.embedding_agent = EmbeddingAgent()
        self.match_evaluator = MatchEvaluatorAgent()
        self.skill_recommender = SkillRecommenderAgent()
        
        # Initialize MongoDB service
        self.mongodb = MongoDBService()
        
        # Initialize Pinecone service
        self.pinecone = PineconeService()
        
        # Build workflow graph
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """
        Build the LangGraph StateGraph workflow.
        
        Returns:
            Compiled StateGraph workflow
        """
        logger.info("Building LangGraph workflow")
        
        # Create state graph
        workflow = StateGraph(GraphState)
        
        # Add nodes
        workflow.add_node("extract_jd", self._extract_jd_node)
        workflow.add_node("analyze_resumes", self._analyze_resumes_node)
        workflow.add_node("generate_embeddings", self._generate_embeddings_node)
        workflow.add_node("evaluate_matches", self._evaluate_matches_node)
        workflow.add_node("recommend_skills", self._recommend_skills_node)
        workflow.add_node("finalize_output", self._finalize_output_node)
        
        # Define workflow edges
        workflow.set_entry_point("extract_jd")
        workflow.add_edge("extract_jd", "analyze_resumes")
        workflow.add_edge("analyze_resumes", "generate_embeddings")
        workflow.add_edge("generate_embeddings", "evaluate_matches")
        workflow.add_edge("evaluate_matches", "recommend_skills")
        workflow.add_edge("recommend_skills", "finalize_output")
        workflow.add_edge("finalize_output", END)
        
        # Compile the workflow
        compiled = workflow.compile()
        logger.info("Successfully built and compiled LangGraph workflow")
        
        return compiled

    async def _extract_jd_node(self, state: GraphState) -> GraphState:
        """
        Node 1: Extract structured data from job description.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state with jd_data
        """
        try:
            logger.info("Node 1: Extracting job description data")
            
            jd_data = await self.jd_extractor.extract_jd_data(state["jd_text"])
            
            state["jd_data"] = jd_data
            logger.info(f"Successfully extracted JD data: {jd_data.get('job_title', 'Unknown')}")
            
        except Exception as e:
            logger.error(f"Error in extract_jd_node: {e}")
            state["error"] = f"JD extraction failed: {str(e)}"
            state["jd_data"] = None
        
        return state

    async def _analyze_resumes_node(self, state: GraphState) -> GraphState:
        """
        Node 2: Analyze and parse resume PDFs.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state with resume_data
        """
        try:
            logger.info(f"Node 2: Analyzing {len(state['resume_files'])} resumes")
            
            resume_data = await self.resume_analyzer.analyze_batch(state["resume_files"])
            
            state["resume_data"] = resume_data
            logger.info(f"Successfully analyzed {len(resume_data)} resumes")
            
        except Exception as e:
            logger.error(f"Error in analyze_resumes_node: {e}")
            state["error"] = f"Resume analysis failed: {str(e)}"
            state["resume_data"] = []
        
        return state

    async def _generate_embeddings_node(self, state: GraphState) -> GraphState:
        """
        Node 3: Generate embeddings for JD and resumes.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state with embeddings
        """
        try:
            logger.info("Node 3: Generating embeddings")
            
            # Generate JD embedding
            jd_embedding = None
            if state["jd_data"]:
                jd_embedding = await self.embedding_agent.embed_jd(state["jd_data"])
            
            state["jd_embedding"] = jd_embedding
            
            # Generate resume embeddings
            if state["resume_data"]:
                resume_embeddings = await self.embedding_agent.embed_batch_resumes(
                    state["resume_data"]
                )
                state["resume_embeddings"] = resume_embeddings
            else:
                state["resume_embeddings"] = []
            
            logger.info(
                f"Successfully generated embeddings: "
                f"JD={'✓' if jd_embedding else '✗'}, "
                f"Resumes={len(state['resume_embeddings'])}"
            )
            
        except Exception as e:
            logger.error(f"Error in generate_embeddings_node: {e}")
            state["error"] = f"Embedding generation failed: {str(e)}"
            state["jd_embedding"] = None
            state["resume_embeddings"] = []
        
        return state

    async def _evaluate_matches_node(self, state: GraphState) -> GraphState:
        """
        Node 4: Evaluate matches between resumes and JD.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state with match_results
        """
        try:
            logger.info("Node 4: Evaluating matches")
            
            if not state["jd_embedding"] or not state["resume_embeddings"]:
                logger.warning("Missing embeddings, cannot evaluate matches")
                state["match_results"] = []
                return state
            
            match_results = await self.match_evaluator.evaluate_batch(
                state["resume_embeddings"],
                state["jd_data"],
                state["jd_embedding"]
            )
            
            state["match_results"] = match_results
            logger.info(f"Successfully evaluated {len(match_results)} matches")
            
        except Exception as e:
            logger.error(f"Error in evaluate_matches_node: {e}")
            state["error"] = f"Match evaluation failed: {str(e)}"
            state["match_results"] = []
        
        return state

    async def _recommend_skills_node(self, state: GraphState) -> GraphState:
        """
        Node 5: Generate skill recommendations for potential candidates.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state with skill_gaps in match_results
        """
        try:
            logger.info("Node 5: Generating skill recommendations")
            
            if not state["match_results"]:
                logger.warning("No match results, skipping recommendations")
                return state
            
            # Create resume data dictionary for lookup
            resume_data_dict = {
                rd.get("resume_id"): rd
                for rd in state["resume_data"]
            }
            
            # Generate recommendations
            updated_results = await self.skill_recommender.recommend_batch(
                state["match_results"],
                state["jd_data"],
                resume_data_dict
            )
            
            state["match_results"] = updated_results
            logger.info("Successfully generated skill recommendations")
            
        except Exception as e:
            logger.error(f"Error in recommend_skills_node: {e}")
            state["error"] = f"Skill recommendation failed: {str(e)}"
        
        return state

    async def _finalize_output_node(self, state: GraphState) -> GraphState:
        """
        Node 6: Finalize output and store in MongoDB.
        
        Args:
            state: Current graph state
            
        Returns:
            Updated state with final_output
        """
        try:
            logger.info("Node 6: Finalizing output and storing in MongoDB")
            
            matches = state["match_results"]
            
            # Calculate statistics
            total_resumes = len(matches)
            high_matches = sum(1 for m in matches if m.get("match_score", 0) >= 80)
            potential_matches = sum(
                1 for m in matches if 65 <= m.get("match_score", 0) < 80
            )
            
            # Build final output
            final_output = {
                "matches": matches,
                "total_resumes": total_resumes,
                "high_matches": high_matches,
                "potential_matches": potential_matches
            }
            
            state["final_output"] = final_output
            
            # Store in MongoDB
            try:
                await self.mongodb.connect()
                await self.mongodb.store_match_result(
                    jd_text=state["jd_text"],
                    jd_data=state["jd_data"],
                    matches=matches
                )
                logger.info("Successfully stored results in MongoDB")
            except Exception as e:
                logger.error(f"Failed to store in MongoDB: {e}")
            
            logger.info(
                f"Finalized output: {total_resumes} total, "
                f"{high_matches} high matches, {potential_matches} potential"
            )
            
        except Exception as e:
            logger.error(f"Error in finalize_output_node: {e}")
            state["error"] = f"Output finalization failed: {str(e)}"
            state["final_output"] = {
                "matches": [],
                "total_resumes": 0,
                "high_matches": 0,
                "potential_matches": 0
            }
        
        return state

    async def execute(
        self,
        jd_text: str,
        resume_files: List[str]
    ) -> Dict[str, Any]:
        """
        Execute the complete resume matching workflow.
        
        Args:
            jd_text: Job description text
            resume_files: List of resume file paths
            
        Returns:
            Final output with matches and statistics
        """
        try:
            logger.info(f"Starting workflow execution for {len(resume_files)} resumes")
            
            # Initialize state
            initial_state: GraphState = {
                "jd_text": jd_text,
                "resume_files": resume_files,
                "jd_data": None,
                "resume_data": [],
                "jd_embedding": None,
                "resume_embeddings": [],
                "match_results": [],
                "final_output": None,
                "error": None
            }
            
            # Execute workflow
            final_state = await self.workflow.ainvoke(initial_state)
            
            if final_state.get("error"):
                logger.error(f"Workflow completed with error: {final_state['error']}")
            else:
                logger.info("Workflow completed successfully")
            
            return final_state.get("final_output", {
                "matches": [],
                "total_resumes": 0,
                "high_matches": 0,
                "potential_matches": 0
            })
            
        except Exception as e:
            logger.error(f"Fatal error in workflow execution: {e}")
            return {
                "matches": [],
                "total_resumes": 0,
                "high_matches": 0,
                "potential_matches": 0,
                "error": str(e)
            }
        finally:
            # Close MongoDB connection
            try:
                await self.mongodb.close()
            except Exception:
                pass

    async def search_database(
        self,
        jd_text: str,
        min_match_score: float = 80.0,
        top_k: int = 100
    ) -> Dict[str, Any]:
        """
        Search stored resumes in database by job description.
        
        This method performs semantic search against previously stored resumes,
        evaluating them against the JD with the same matching algorithm.
        Only returns resumes with match scores >= min_match_score.
        
        Args:
            jd_text: Job description text
            min_match_score: Minimum match score threshold (0-100)
            top_k: Maximum number of resumes to retrieve from database
            
        Returns:
            Final output with matched resumes and statistics
        """
        try:
            logger.info(f"Starting database search: min_score={min_match_score}%, top_k={top_k}")
            
            # Step 1: Extract JD data
            jd_data = await self.jd_extractor.extract_jd_data(jd_text)
            if not jd_data:
                logger.error("Failed to extract JD data")
                return {
                    "matches": [],
                    "total_resumes": 0,
                    "high_matches": 0,
                    "potential_matches": 0,
                    "error": "JD extraction failed"
                }
            
            # Step 2: Generate JD embedding
            jd_embedding = await self.embedding_agent.embed_jd(jd_data)
            if not jd_embedding:
                logger.error("Failed to generate JD embedding")
                return {
                    "matches": [],
                    "total_resumes": 0,
                    "high_matches": 0,
                    "potential_matches": 0,
                    "error": "JD embedding generation failed"
                }
            
            # Step 3: Search Pinecone for similar resumes
            # Convert match percentage to similarity score (0-1 range)
            min_similarity = 0.5  # Start with broader search
            
            stored_resumes = await self.pinecone.search_by_jd(
                jd_embedding=jd_embedding,
                top_k=top_k,
                min_similarity=min_similarity
            )
            
            if not stored_resumes:
                logger.info("No resumes found in database")
                return {
                    "matches": [],
                    "total_resumes": 0,
                    "high_matches": 0,
                    "potential_matches": 0
                }
            
            logger.info(f"Retrieved {len(stored_resumes)} resumes from database")
            
            # Step 4: Evaluate matches
            # Create resume_embeddings format for evaluator
            resume_embeddings = []
            for resume in stored_resumes:
                # Generate embedding for complete evaluation
                resume_text = await self.embedding_agent._create_resume_text(resume)
                resume_embedding = await self.embedding_agent.embed_text(resume_text)
                
                resume_embeddings.append({
                    "resume_data": resume,
                    "embedding": resume_embedding
                })
            
            match_results = await self.match_evaluator.evaluate_batch(
                resume_embeddings,
                jd_data,
                jd_embedding
            )
            
            # Step 5: Filter by minimum match score
            filtered_matches = [
                match for match in match_results
                if match.get("match_score", 0) >= min_match_score
            ]
            
            logger.info(f"Filtered to {len(filtered_matches)} matches >= {min_match_score}%")
            
            # Step 6: Generate skill recommendations for potential candidates
            resume_data_dict = {
                resume.get("resume_id"): resume
                for resume in stored_resumes
            }
            
            updated_matches = await self.skill_recommender.recommend_batch(
                filtered_matches,
                jd_data,
                resume_data_dict
            )
            
            # Step 7: Calculate statistics
            total_resumes = len(filtered_matches)
            high_matches = sum(1 for m in updated_matches if m.get("match_score", 0) >= 80)
            potential_matches = sum(
                1 for m in updated_matches if 65 <= m.get("match_score", 0) < 80
            )
            
            final_output = {
                "matches": updated_matches,
                "total_resumes": total_resumes,
                "high_matches": high_matches,
                "potential_matches": potential_matches
            }
            
            # Step 8: Store search results in MongoDB
            try:
                await self.mongodb.connect()
                await self.mongodb.store_match_result(
                    jd_text=jd_text,
                    jd_data=jd_data,
                    matches=updated_matches
                )
                logger.info("Successfully stored database search results in MongoDB")
            except Exception as e:
                logger.error(f"Failed to store in MongoDB: {e}")
            finally:
                await self.mongodb.close()
            
            logger.info(
                f"Database search completed: {total_resumes} matches, "
                f"{high_matches} high matches, {potential_matches} potential"
            )
            
            return final_output
            
        except Exception as e:
            logger.error(f"Database search failed: {e}", exc_info=True)
            return {
                "matches": [],
                "total_resumes": 0,
                "high_matches": 0,
                "potential_matches": 0,
                "error": str(e)
            }

    async def store_resumes(
        self,
        resume_files: List[str]
    ) -> Dict[str, Any]:
        """
        Store resumes in Pinecone database for future searches.
        
        Processes resume PDFs, generates embeddings, and stores them
        in Pinecone with metadata for semantic search.
        
        Args:
            resume_files: List of resume file paths
            
        Returns:
            Dictionary with storage statistics
        """
        try:
            logger.info(f"Starting resume storage for {len(resume_files)} files")
            
            # Step 1: Analyze resumes
            resume_data_list = await self.resume_analyzer.analyze_batch(resume_files)
            
            if not resume_data_list:
                logger.warning("No resumes were successfully analyzed")
                return {
                    "stored_count": 0,
                    "failed_count": len(resume_files)
                }
            
            logger.info(f"Successfully analyzed {len(resume_data_list)} resumes")
            
            # Step 2: Generate embeddings
            resume_embeddings = await self.embedding_agent.embed_batch_resumes(
                resume_data_list
            )
            
            # Step 3: Store in Pinecone
            stored_count = 0
            failed_count = 0
            
            for item in resume_embeddings:
                resume_data = item.get("resume_data", {})
                embedding = item.get("embedding", [])
                resume_id = resume_data.get("resume_id", "unknown")
                
                if not embedding:
                    logger.warning(f"Skipping {resume_id}: No embedding generated")
                    failed_count += 1
                    continue
                
                success = await self.pinecone.store_resume_embedding(
                    resume_id=resume_id,
                    embedding=embedding,
                    resume_data=resume_data
                )
                
                if success:
                    stored_count += 1
                else:
                    failed_count += 1
            
            logger.info(
                f"Storage completed: {stored_count} stored, {failed_count} failed"
            )
            
            return {
                "stored_count": stored_count,
                "failed_count": failed_count
            }
            
        except Exception as e:
            logger.error(f"Resume storage failed: {e}", exc_info=True)
            return {
                "stored_count": 0,
                "failed_count": len(resume_files),
                "error": str(e)
            }
