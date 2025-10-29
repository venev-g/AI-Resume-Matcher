from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from app.graph.state import ResumeMatchingState
from app.graph.nodes import (
    extract_resume_skills_node,
    validate_resume_skills_node,
    classify_resume_skills_node,
    extract_jd_skills_node,
    validate_jd_skills_node,
    classify_jd_skills_node,
    sync_barrier_node,
    match_skills_node,
    generate_suggestions_node
)

def create_resume_matching_workflow() -> StateGraph:
    """Create the LangGraph workflow for resume-JD matching"""
    
    # Create the state graph
    workflow = StateGraph(ResumeMatchingState)
    
    # Add nodes to the graph
    workflow.add_node("extract_resume_skills", extract_resume_skills_node)
    workflow.add_node("validate_resume_skills", validate_resume_skills_node)
    workflow.add_node("classify_resume_skills", classify_resume_skills_node)
    workflow.add_node("extract_jd_skills", extract_jd_skills_node)
    workflow.add_node("validate_jd_skills", validate_jd_skills_node)
    workflow.add_node("classify_jd_skills", classify_jd_skills_node)
    workflow.add_node("sync_barrier", sync_barrier_node)
    workflow.add_node("match_skills", match_skills_node)
    workflow.add_node("generate_suggestions", generate_suggestions_node)
    
    # Define the workflow edges
    
    # Resume processing branch
    workflow.add_edge(START, "extract_resume_skills")
    workflow.add_edge("extract_resume_skills", "validate_resume_skills")
    workflow.add_edge("validate_resume_skills", "classify_resume_skills")
    workflow.add_edge("classify_resume_skills", "sync_barrier")
    
    # JD processing branch (parallel)
    workflow.add_edge(START, "extract_jd_skills")
    workflow.add_edge("extract_jd_skills", "validate_jd_skills")
    workflow.add_edge("validate_jd_skills", "classify_jd_skills")
    workflow.add_edge("classify_jd_skills", "sync_barrier")
    
    # After synchronization, proceed with matching
    workflow.add_edge("sync_barrier", "match_skills")
    workflow.add_edge("match_skills", "generate_suggestions")
    workflow.add_edge("generate_suggestions", END)
    
    return workflow

def create_batch_matching_workflow() -> StateGraph:
    """Create workflow for batch processing multiple resumes against one JD"""
    
    # This would be a more complex workflow for handling multiple resumes
    # For now, we'll use the single matching workflow and call it multiple times
    return create_resume_matching_workflow()

# Compile the workflows
resume_matching_graph = create_resume_matching_workflow().compile()
batch_matching_graph = create_batch_matching_workflow().compile()
