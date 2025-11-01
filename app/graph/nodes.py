import json
import logging
from typing import Dict, Any
from app.graph.state import ResumeMatchingState
from app.graph.prompts import (
    enhanced_skill_extraction_prompt,
    enhanced_skill_matching_prompt,
    skill_gap_suggestions_prompt,
)
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


async def extract_resume_skills_node(state: ResumeMatchingState) -> Dict[str, Any]:
    """Extract skills from resume document"""
    try:
        logger.info(f"Extracting skills from resume {state['resume_id']}")

        prompt = enhanced_skill_extraction_prompt(
            state["resume_doc"], document_type="resume"
        )

        result = await llm_service.call_llm(prompt)

        logger.info("Resume skill extraction completed")
        return {"extracted_resume_skills_json": result}

    except Exception as e:
        logger.error(f"Error extracting resume skills: {str(e)}")
        return {
            "processing_status": "error",
            "error_message": f"Resume skill extraction failed: {str(e)}",
        }


async def validate_resume_skills_node(state: ResumeMatchingState) -> Dict[str, Any]:
    """Validate extracted resume skills"""
    try:
        logger.info(f"Validating resume skills for {state['resume_id']}")

        # For now, we'll use the extracted skills as validated
        # In a production system, you might implement additional validation logic
        validated_skills = state["extracted_resume_skills_json"]

        logger.info("Resume skill validation completed")
        return {"validated_resume_skills_json": validated_skills}

    except Exception as e:
        logger.error(f"Error validating resume skills: {str(e)}")
        return {
            "processing_status": "error",
            "error_message": f"Resume skill validation failed: {str(e)}",
        }


async def classify_resume_skills_node(state: ResumeMatchingState) -> Dict[str, Any]:
    """Classify resume skills as technical/non-technical"""
    try:
        logger.info(f"Classifying resume skills for {state['resume_id']}")

        # Use the skill classification prompt from the original project
        from app.graph.prompts import skill_type_classification

        prompt = skill_type_classification(state["validated_resume_skills_json"])
        result = await llm_service.call_llm(prompt)

        logger.info("Resume skill classification completed")
        return {"classified_resume_skills_json": result}

    except Exception as e:
        logger.error(f"Error classifying resume skills: {str(e)}")
        return {
            "processing_status": "error",
            "error_message": f"Resume skill classification failed: {str(e)}",
        }


async def extract_jd_skills_node(state: ResumeMatchingState) -> Dict[str, Any]:
    """Extract skills from job description"""
    try:
        logger.info(f"Extracting skills from JD {state['jd_id']}")

        prompt = enhanced_skill_extraction_prompt(
            state["job_description_doc"], document_type="job_description"
        )

        result = await llm_service.call_llm(prompt)

        logger.info("JD skill extraction completed")
        return {"extracted_jd_skills_json": result}

    except Exception as e:
        logger.error(f"Error extracting JD skills: {str(e)}")
        return {
            "processing_status": "error",
            "error_message": f"JD skill extraction failed: {str(e)}",
        }


async def validate_jd_skills_node(state: ResumeMatchingState) -> Dict[str, Any]:
    """Validate extracted JD skills"""
    try:
        logger.info(f"Validating JD skills for {state['jd_id']}")

        validated_skills = state["extracted_jd_skills_json"]

        logger.info("JD skill validation completed")
        return {"validated_jd_skills_json": validated_skills}

    except Exception as e:
        logger.error(f"Error validating JD skills: {str(e)}")
        return {
            "processing_status": "error",
            "error_message": f"JD skill validation failed: {str(e)}",
        }


async def classify_jd_skills_node(state: ResumeMatchingState) -> Dict[str, Any]:
    """Classify JD skills as technical/non-technical"""
    try:
        logger.info(f"Classifying JD skills for {state['jd_id']}")

        from app.graph.prompts import skill_type_classification

        prompt = skill_type_classification(state["validated_jd_skills_json"])
        result = await llm_service.call_llm(prompt)

        logger.info("JD skill classification completed")
        return {"classified_jd_skills_json": result}

    except Exception as e:
        logger.error(f"Error classifying JD skills: {str(e)}")
        return {
            "processing_status": "error",
            "error_message": f"JD skill classification failed: {str(e)}",
        }


async def sync_barrier_node(state: ResumeMatchingState) -> Dict[str, Any]:
    """Synchronization barrier to ensure both skill extraction paths complete"""
    logger.info("Synchronization barrier: Both skill extractions complete")
    return {"processing_status": "skills_synchronized"}


async def match_skills_node(state: ResumeMatchingState) -> Dict[str, Any]:
    """Perform comprehensive skill matching"""
    try:
        logger.info(
            f"Matching skills for resume {state['resume_id']} against JD {state['jd_id']}"
        )

        prompt = enhanced_skill_matching_prompt(
            state["classified_resume_skills_json"], state["classified_jd_skills_json"]
        )

        result = await llm_service.call_llm(prompt)

        # Parse the result to extract key metrics
        try:
            match_data = json.loads(result)
            match_percentage = match_data.get("overall_match_percentage", 0.0)

            # Extract skill lists from the detailed analysis
            skill_analysis = match_data.get("skill_analysis", {})
            matched_skills = [
                item["skill"] for item in skill_analysis.get("perfect_matches", [])
            ]
            matched_skills.extend(
                [item["skill"] for item in skill_analysis.get("good_matches", [])]
            )

            missing_skills = [
                item["skill"] for item in skill_analysis.get("missing_critical", [])
            ]
            missing_skills.extend(
                [item["skill"] for item in skill_analysis.get("missing_preferred", [])]
            )

            additional_skills = [
                item["skill"] for item in skill_analysis.get("bonus_skills", [])
            ]

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Error parsing match result: {e}. Using defaults.")
            match_percentage = 0.0
            matched_skills = []
            missing_skills = []
            additional_skills = []

        logger.info(f"Skill matching completed. Match percentage: {match_percentage}%")
        return {
            "skill_comparison_json": result,
            "match_percentage": match_percentage,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "additional_skills": additional_skills,
            "processing_status": "skills_matched",
        }

    except Exception as e:
        logger.error(f"Error matching skills: {str(e)}")
        return {
            "processing_status": "error",
            "error_message": f"Skill matching failed: {str(e)}",
        }


async def generate_suggestions_node(state: ResumeMatchingState) -> Dict[str, Any]:
    """Generate skill gap suggestions for improvement"""
    try:
        match_percentage = state.get("match_percentage", 0.0)

        # Only generate suggestions if match is below threshold
        if match_percentage >= 80.0:
            logger.info(
                f"Match percentage {match_percentage}% is above threshold. No suggestions needed."
            )
            return {
                "suggestions_json": json.dumps(
                    {
                        "message": "Match percentage is above 80%. No skill gap suggestions needed.",
                        "match_percentage": match_percentage,
                    }
                ),
                "processing_status": "suggestions_complete",
            }

        logger.info(f"Generating skill gap suggestions for {match_percentage}% match")

        prompt = skill_gap_suggestions_prompt(
            state["classified_resume_skills_json"],
            state["classified_jd_skills_json"],
            match_percentage,
        )

        result = await llm_service.call_llm(prompt)

        logger.info("Skill gap suggestions generated")
        return {"suggestions_json": result, "processing_status": "suggestions_complete"}

    except Exception as e:
        logger.error(f"Error generating suggestions: {str(e)}")
        return {
            "processing_status": "error",
            "error_message": f"Suggestion generation failed: {str(e)}",
        }


# Add the skill_type_classification function from original prompts.py
def skill_type_classification(validated_skills):
    return f"""# SYSTEM ROLE

You are an expert Skills Taxonomy Classifier specializing in resume analysis and candidate evaluation.

# TASK

Classify each skill in the provided list as either "Technical" or "Non-Technical" by adding a `skill_class` key to each dictionary entry.

# INPUT FORMAT

You will receive a list of dictionaries, where each dictionary contains:
- `skill`: Name of the skill
- `years_of_experience`: Duration of experience with the skill
- `justification`: Context explaining why this skill was identified

# CLASSIFICATION CRITERIA

## Technical Skills
Skills that involve:
- Programming languages (Python, Java, C++, JavaScript, etc.)
- Software frameworks and libraries (React, Django, TensorFlow, etc.)
- Database technologies (SQL, MongoDB, PostgreSQL, etc.)
- Cloud platforms (AWS, Azure, GCP, etc.)
- DevOps and infrastructure tools (Docker, Kubernetes, Jenkins, etc.)
- Data science and analytics tools (Pandas, R, Tableau, Power BI, etc.)
- Operating systems and networking technologies
- Hardware and electronics knowledge
- Engineering tools (CAD, MATLAB, AutoCAD, etc.)
- Cybersecurity tools and methodologies
- Mobile development platforms (iOS, Android, Flutter, etc.)
- Version control systems (Git, SVN, etc.)
- Testing frameworks and tools
- API technologies (REST, GraphQL, SOAP, etc.)
- Any domain-specific technical expertise

## Non-Technical Skills
Skills that involve:
- Communication (written, verbal, presentation, etc.)
- Leadership and management
- Interpersonal abilities (teamwork, collaboration, networking, etc.)
- Organizational skills (time management, project management, planning, etc.)
- Creative abilities (design thinking, creativity, content creation, etc.)
- Sales and marketing
- Customer service and relationship management
- Problem-solving and critical thinking (when not technical in nature)
- Adaptability and flexibility
- Emotional intelligence
- Negotiation and conflict resolution
- Business acumen and strategy
- Language proficiencies

# OUTPUT REQUIREMENTS

1. **Preserve All Input Data**: Return the EXACT same structure with all original keys and values intact
2. **Add Classification**: Include ONLY one new key: `skill_class` with value "Technical" or "Non-Technical"
3. **Strict JSON Format**: Output must be valid JSON
4. **No Modifications**: Do NOT alter, summarize, or skip any existing data
5. **Complete Processing**: Classify ALL skills in the input list

# EDGE CASES

- **Hybrid Skills** (e.g., "Technical Writing", "Data Analysis"): If the skill has technical components or requires technical knowledge, classify as "Technical"
- **Tools for Non-Technical Work** (e.g., "Microsoft Word", "Email"): Classify as "Non-Technical"
- **Unclear Skills**: Use the justification field to inform classification
- **Domain-Specific Skills**: Consider the technical vs. business nature (e.g., "Financial Modeling" with Excel = Technical)

# INSTRUCTIONS

1. Read the entire input list
2. Analyze each skill based on the criteria above
3. Add the `skill_class` key with appropriate value
4. Return the complete JSON with all original data preserved
5. Ensure valid JSON syntax (proper quotes, commas, brackets)

# INPUT SKILLS DATA:
{validated_skills}"""
