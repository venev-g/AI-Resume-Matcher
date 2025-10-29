def enhanced_skill_extraction_prompt(document_text: str, document_type: str = "resume") -> str:
    """Enhanced skill extraction prompt for both resumes and job descriptions"""
    return f"""
# ADVANCED SKILL EXTRACTION SPECIALIST

## ROLE AND EXPERTISE
You are an elite AI Skills Extraction Specialist with 20+ years of experience in talent acquisition, competency mapping, and technical assessment across all industries.

## TASK OBJECTIVE
Extract ALL skills mentioned explicitly in the provided {document_type} with maximum precision and granularity. For each skill identified, determine experience level/requirements and provide detailed justification.

## EXTRACTION GUIDELINES

### 1. COMPREHENSIVE SKILL CATEGORIES

#### Technical Skills (High Priority)
- Programming languages (Python, Java, JavaScript, C++, Go, Rust, etc.)
- Frameworks & Libraries (React, Angular, Django, Spring, TensorFlow, PyTorch, etc.)
- Databases (MySQL, PostgreSQL, MongoDB, Redis, Elasticsearch, etc.)
- Cloud Platforms (AWS, Azure, GCP, Oracle Cloud, IBM Cloud, etc.)
- DevOps & Infrastructure (Docker, Kubernetes, Jenkins, Terraform, Ansible, etc.)
- Development Tools (Git, JIRA, VS Code, IntelliJ, Postman, etc.)
- Operating Systems (Linux, Windows, macOS, Unix variants, etc.)
- Networking & Security (TCP/IP, SSL/TLS, VPN, Firewalls, OAuth, etc.)
- Data & Analytics (Pandas, NumPy, Tableau, Power BI, Apache Spark, etc.)
- Mobile Development (iOS, Android, React Native, Flutter, Xamarin, etc.)
- Web Technologies (HTML, CSS, REST APIs, GraphQL, WebSockets, etc.)
- Testing & QA (Selenium, Jest, JUnit, Cypress, Postman, etc.)

#### Domain & Industry Skills
- Business Intelligence & Analytics
- Machine Learning & AI
- Cybersecurity & Information Security
- Financial Analysis & Modeling
- Healthcare & Medical Knowledge
- Supply Chain & Logistics
- Digital Marketing & SEO
- Project Management Methodologies (Agile, Scrum, Kanban, Waterfall, etc.)
- Compliance & Regulatory (GDPR, HIPAA, SOX, PCI-DSS, etc.)

#### Professional & Soft Skills (Extract ONLY if explicitly mentioned)
- Leadership & Team Management
- Communication (written, verbal, presentation)
- Problem-solving & Critical Thinking
- Client/Customer Relationship Management
- Cross-functional Collaboration
- Strategic Planning & Execution
- Change Management
- Mentoring & Training

#### Certifications & Qualifications
- Professional Certifications (AWS, Azure, Google Cloud, Cisco, etc.)
- Industry Certifications (PMP, Scrum Master, CISSP, etc.)
- Academic Qualifications (if relevant to skills)
- Licenses & Accreditations

### 2. EXPERIENCE/REQUIREMENT CALCULATION

#### For Resumes:
- **Explicit Duration**: "5 years of Python experience" → 5.0 years
- **Job Timeline Analysis**: Calculate from employment dates where skill is mentioned
- **Multiple Roles**: SUM non-overlapping experience across roles
- **Current Roles**: Calculate up to October 2025
- **Project Experience**: Include if explicitly mentioned with timeframes
- **Academic Experience**: Weight at 50% (2 years academic = 1 year professional)
- **No Clear Timeline**: Assign "Unknown" with detailed justification

#### For Job Descriptions:
- **Required Experience**: "3+ years of Java" → "3+ years required"
- **Preferred vs Required**: Distinguish between must-have and nice-to-have
- **Proficiency Levels**: "Expert in Python" → "Expert level required"
- **General Mentions**: "Experience with AWS" → "Experience required"

### 3. ENHANCED JUSTIFICATION REQUIREMENTS

Each skill MUST include comprehensive justification with:

#### Source Identification:
- **Exact Location**: "Found in Technical Skills section, line 15"
- **Context**: "Mentioned in Senior Developer role at TechCorp Inc"
- **Usage Context**: "Used for backend API development and microservices"

#### Experience/Requirement Calculation:
- **Mathematical Breakdown**: Show complete calculation logic
- **Multiple Sources**: Reference all occurrences if applicable
- **Assumptions Made**: Clearly state any assumptions in calculation

#### Relevance Assessment:
- **Skill Importance**: Technical vs supporting skill
- **Application Context**: How skill was applied or will be applied
- **Proficiency Indicators**: Beginner, intermediate, advanced, expert

### 4. ADVANCED EXTRACTION RULES

#### DO Extract:
- Every skill mentioned, regardless of frequency
- Skill variations and normalize appropriately
- Tools, technologies, methodologies, certifications
- Industry-specific knowledge and domain expertise
- Soft skills ONLY if explicitly stated
- Programming paradigms (OOP, Functional, etc.)
- Architecture patterns (Microservices, MVC, etc.)

#### DO NOT Extract:
- Job titles or company names (unless they represent specific technologies)
- Educational degrees (unless they represent specific technical knowledge)
- Generic responsibilities without specific skills
- Inferred capabilities not explicitly mentioned
- Location names or personal information

### 5. NORMALIZATION & STANDARDIZATION

#### Skill Name Normalization:
- "JavaScript" and "JS" → "JavaScript"
- "React.js" and "ReactJS" → "React"
- "Machine Learning" and "ML" → "Machine Learning"
- "Amazon Web Services" and "AWS" → "AWS"

#### Experience Standardization:
- Use decimal precision (2.5 years, 3.8 years)
- Round to nearest 0.1 year for calculated values
- Use "Unknown" for insufficient information
- Use specific ranges for JD requirements ("2-5 years")

### 6. OUTPUT FORMAT

Return a valid JSON array with the following structure:

[
{{
"skill": "Python",
"years_of_experience": 5.5,
"justification": "Found in Technical Skills section and mentioned in 3 job roles: (1) Software Engineer at ABC Corp (Jan 2020 - Dec 2022): 3 years for backend development, (2) Senior Developer at XYZ Inc (Jan 2023 - Present): 2.8 years for API development. Total: 5.8 years, rounded to 5.5 accounting for 3-month gap. Used for Django framework development and data processing pipelines."
}},
{{
"skill": "AWS",
"years_of_experience": "3+ years required",
"justification": "Listed in Required Qualifications section as 'Minimum 3 years of AWS cloud experience required'. Also mentioned in job responsibilities for 'designing scalable cloud solutions using AWS services including EC2, S3, and Lambda'."
}}
]


### 7. QUALITY VALIDATION CHECKLIST

Before finalizing output:
- ✅ Every skill has detailed, specific justification
- ✅ All experience calculations are mathematically accurate
- ✅ No duplicate skills (properly normalized)
- ✅ JSON format is valid and parseable
- ✅ All skills are explicitly mentioned in source document
- ✅ Justifications include source location and context
- ✅ Experience values are realistic and well-reasoned

## DOCUMENT TYPE: {document_type.upper()}

## INPUT DOCUMENT:
{document_text}

## CRITICAL INSTRUCTIONS:
1. Be EXHAUSTIVE - extract every skill mentioned
2. Be PRECISE - show detailed calculation work  
3. Be CONSERVATIVE - use lower estimates when ambiguous
4. Be CONSISTENT - apply same rules to all skills
5. Current date for calculations: October 2025
6. Return ONLY the JSON array, no additional commentary
"""


def enhanced_skill_matching_prompt(resume_skills: str, jd_skills: str) -> str:
    """Enhanced prompt for comprehensive skill matching and scoring"""
    return f"""
# ADVANCED RESUME-JD MATCHING & SCORING SYSTEM

## ROLE AND EXPERTISE
You are an elite Technical Recruitment Analyst and Skills Assessment Expert with 20+ years of experience in candidate evaluation, competency mapping, and job-fit analysis across all industries and technical domains.

## TASK OBJECTIVE
Perform comprehensive skill matching between candidate resume and job description. Calculate precise match percentages, identify gaps, and provide detailed analysis for recruitment decision-making.

## MATCHING METHODOLOGY

### 1. SKILL CATEGORIZATION & WEIGHTING

#### Technical Skills (Weight: 70%)
- **Core Programming Languages**: 25% of total score
- **Frameworks & Technologies**: 20% of total score  
- **Tools & Platforms**: 15% of total score
- **Domain-Specific Technical**: 10% of total score

#### Professional Skills (Weight: 20%)
- **Project Management & Methodologies**: 8% of total score
- **Industry Knowledge & Compliance**: 7% of total score
- **Professional Certifications**: 5% of total score

#### Soft Skills (Weight: 10%)
- **Leadership & Management**: 4% of total score
- **Communication & Collaboration**: 6% of total score

### 2. EXPERIENCE MATCHING ALGORITHM

#### Experience Level Scoring:
- **Exceeds Requirement by 2+ years**: 100% match
- **Meets Requirement exactly**: 90% match
- **80-99% of required experience**: 70% match  
- **50-79% of required experience**: 40% match
- **25-49% of required experience**: 20% match
- **Less than 25% of required experience**: 10% match
- **No experience in required skill**: 0% match

#### Special Cases:
- **"Unknown" resume experience vs specific requirement**: 30% match (benefit of doubt)
- **High experience vs "preferred" requirement**: 95% match
- **Certification without hands-on experience**: 60% match

### 3. SKILL MATCHING RULES

#### Exact Matches (100% skill match):
- Identical skill names after normalization
- Direct technology matches (React = React, Python = Python)

#### Partial Matches (70-90% skill match):
- Related technologies in same category (Angular vs React = 80%)
- Different versions of same technology (Python 2 vs Python 3 = 90%)
- Closely related skills (MySQL vs PostgreSQL = 85%)

#### Domain Matches (50-70% skill match):
- Skills in same domain but different tools (Tableau vs Power BI = 70%)
- Programming languages in same paradigm (Java vs C# = 65%)

#### No Match (0% skill match):
- Completely unrelated skills
- Different technology stacks entirely

### 4. COMPREHENSIVE ANALYSIS REQUIREMENTS

#### Calculate and Provide:
1. **Overall Match Percentage** (0-100%)
2. **Technical Skills Match** (0-100%)  
3. **Professional Skills Match** (0-100%)
4. **Soft Skills Match** (0-100%)
5. **Experience Adequacy Score** (0-100%)

#### Identify and List:
1. **Perfect Matches**: Skills that match exactly with adequate experience
2. **Good Matches**: Skills that match with minor experience gaps
3. **Partial Matches**: Related skills that could transfer
4. **Missing Critical Skills**: Required skills completely absent
5. **Missing Preferred Skills**: Nice-to-have skills that are absent
6. **Bonus Skills**: Additional skills that add value beyond requirements

### 5. DETAILED SKILL GAP ANALYSIS

For each missing skill, provide:
- **Criticality Level**: Critical/Important/Preferred
- **Learning Curve**: Easy/Moderate/Difficult to acquire
- **Alternatives Present**: Similar skills candidate already has
- **Impact on Job Performance**: High/Medium/Low

### 6. RECOMMENDATION ENGINE

#### Match Categories:
- **85-100%**: "Excellent Match - Highly Recommended"
- **75-84%**: "Good Match - Recommended with minor gaps"
- **65-74%**: "Fair Match - Consider with skill development plan"
- **50-64%**: "Below Threshold - Significant gaps present"
- **0-49%**: "Poor Match - Not recommended"

### 7. OUTPUT FORMAT

Return a comprehensive JSON object with the following structure:

{{
"overall_match_percentage": 82.5,
"match_category": "Good Match - Recommended with minor gaps",
"detailed_scores": {{
"technical_skills_match": 85.0,
"professional_skills_match": 78.0,
"soft_skills_match": 90.0,
"experience_adequacy": 80.0
}},
"skill_analysis": {{
"perfect_matches": [
{{
"skill": "Python",
"resume_experience": "5.5 years",
"jd_requirement": "3+ years required",
"match_score": 100,
"notes": "Exceeds requirement significantly"
}}
],
"good_matches": [
{{
"skill": "React",
"resume_experience": "2.0 years",
"jd_requirement": "2+ years required",
"match_score": 90,
"notes": "Meets requirement exactly"
}}
],
"partial_matches": [
{{
"skill": "Angular",
"resume_equivalent": "React",
"match_score": 80,
"notes": "Has React experience which transfers well to Angular"
}}
],
"missing_critical": [
{{
"skill": "Kubernetes",
"requirement": "2+ years required",
"criticality": "Critical",
"learning_curve": "Moderate",
"alternatives": ["Docker experience provides foundation"]
}}
],
"missing_preferred": [
{{
"skill": "GraphQL",
"requirement": "Preferred",
"criticality": "Preferred",
"learning_curve": "Easy",
"alternatives": ["Strong REST API experience"]
}}
],
"bonus_skills": [
{{
"skill": "Machine Learning",
"resume_experience": "2.0 years",
"value_add": "High - Could enhance data-driven features"
}}
]
}},
"experience_analysis": {{
"meets_minimum_requirements": true,
"total_relevant_years": 7.5,
"experience_gaps": [
"Cloud infrastructure management needs development",
"DevOps practices could be strengthened"
],
"experience_strengths": [
"Strong programming foundation",
"Solid web development experience"
]
}},
"recommendations": {{
"hire_recommendation": "Recommended with skill development plan",
"key_strengths": [
"Excellent programming skills",
"Good cultural fit based on soft skills",
"Experience exceeds core requirements"
],
"development_priorities": [
"Kubernetes certification and hands-on experience",
"Cloud architecture patterns",
"DevOps automation tools"
],
"estimated_ramp_time": "2-3 months for full productivity",
"training_recommendations": [
"Kubernetes certification course",
"Cloud architecture workshop",
"DevOps bootcamp"
]
}},
"statistical_summary": {{
"total_jd_skills": 25,
"total_resume_skills": 22,
"matched_skills_count": 18,
"missing_skills_count": 7,
"bonus_skills_count": 4,
"match_confidence": "High - Based on comprehensive analysis"
}}
}}


## INPUT DATA

**RESUME SKILLS:**
{resume_skills}

**JOB DESCRIPTION REQUIREMENTS:**
{jd_skills}

## CRITICAL INSTRUCTIONS:
1. Perform thorough skill-by-skill comparison
2. Apply experience matching algorithm precisely
3. Use weighted scoring methodology  
4. Identify all categories of matches and gaps
5. Provide actionable recommendations
6. Ensure mathematical accuracy in all calculations
7. Return ONLY the JSON object, no additional commentary
8. Be objective and data-driven in assessment
"""


def skill_gap_suggestions_prompt(resume_skills: str, jd_skills: str, match_percentage: float) -> str:
    """Prompt for generating skill improvement suggestions"""
    return f"""
# SKILL GAP ANALYSIS & IMPROVEMENT RECOMMENDATIONS

## ROLE AND EXPERTISE
You are a Senior Career Development Advisor and Skills Enhancement Strategist with 15+ years of experience in talent development, skill gap analysis, and career progression planning.

## TASK OBJECTIVE
Analyze the skill gap between the candidate's current capabilities and job requirements. Provide specific, actionable recommendations to bridge these gaps and improve the match percentage from {match_percentage}% to 80%+ (target threshold).

## GAP ANALYSIS METHODOLOGY

### 1. CRITICAL GAP IDENTIFICATION

#### Prioritization Framework:
1. **Critical Skills** (Must-have for job performance)
   - Required skills completely missing from resume
   - Skills with insufficient experience levels
   - Core technologies for the role

2. **Important Skills** (Significant impact on success)
   - Preferred skills that enhance performance
   - Skills that complement existing capabilities
   - Industry-standard tools and practices

3. **Enhancement Skills** (Career advancement)
   - Skills that exceed basic requirements
   - Emerging technologies in the field
   - Leadership and advanced capabilities

### 2. SKILL ACQUISITION ANALYSIS

For each identified gap, assess:
- **Learning Difficulty**: Beginner/Intermediate/Advanced
- **Time to Proficiency**: Weeks/Months/Years
- **Prerequisites**: What skills/knowledge needed first
- **Learning Resources**: Courses, certifications, projects
- **Practical Application**: How to gain hands-on experience

### 3. IMPROVEMENT ROADMAP

#### Phase 1: Quick Wins (1-3 months)
- Skills that can be learned rapidly
- Certifications that validate existing knowledge
- Tools similar to ones already known

#### Phase 2: Core Development (3-6 months)  
- Fundamental skills requiring deeper learning
- Hands-on project experience
- Professional development activities

#### Phase 3: Advanced Mastery (6-12 months)
- Complex skills requiring extensive practice
- Leadership and strategic capabilities
- Specialized domain expertise

### 4. MATCH PERCENTAGE IMPROVEMENT CALCULATION

Estimate potential match percentage increase for each recommended skill:
- Calculate current gap impact on overall score
- Estimate improvement after skill acquisition
- Project realistic timeline for improvement
- Account for skill transfer and synergies

### 5. OUTPUT FORMAT

Provide comprehensive improvement recommendations in the following JSON structure:

{{
"current_analysis": {{
"current_match_percentage": {match_percentage},
"target_match_percentage": 80.0,
"improvement_needed": "X percentage points",
"primary_gap_areas": [
"Technical Skills",
"Cloud Technologies",
"DevOps Practices"
]
}},
"critical_skill_gaps": [
{{
"skill": "Kubernetes",
"current_level": "None",
"required_level": "2+ years",
"priority": "Critical",
"impact_on_match": 8.5,
"learning_path": {{
"difficulty": "Intermediate",
"time_to_basic_proficiency": "2-3 months",
"prerequisites": ["Docker experience (already has)", "Container concepts"],
"recommended_resources": [
"Kubernetes Official Documentation",
"Certified Kubernetes Administrator (CKA) course",
"Hands-on cluster setup projects"
],
"practical_experience": [
"Set up local Kubernetes cluster",
"Deploy sample applications",
"Practice scaling and monitoring"
]
}},
"quick_start_tips": [
"Leverage existing Docker knowledge",
"Start with minikube for local development",
"Focus on core concepts first"
]
}}
],
"important_skill_gaps": [
{{
"skill": "AWS Lambda",
"current_level": "Basic AWS knowledge",
"required_level": "Serverless experience preferred",
"priority": "Important",
"impact_on_match": 4.0,
"learning_path": {{
"difficulty": "Beginner",
"time_to_basic_proficiency": "3-4 weeks",
"prerequisites": ["Basic AWS knowledge (already has)"],
"recommended_resources": [
"AWS Lambda Developer Guide",
"Serverless Framework tutorials",
"AWS Certified Developer course"
],
"practical_experience": [
"Build simple Lambda functions",
"Create API Gateway integrations",
"Implement event-driven architectures"
]
}}
}}
],
"enhancement_opportunities": [
{{
"skill": "GraphQL",
"current_level": "REST API experience",
"target_level": "GraphQL API development",
"priority": "Enhancement",
"impact_on_match": 2.0,
"rationale": "Would complement existing REST experience and add modern API development skills"
}}
],
"improvement_roadmap": {{
"phase_1_quick_wins": {{
"duration": "1-3 months",
"focus_areas": ["AWS certifications", "Docker containerization", "Basic Kubernetes"],
"expected_match_improvement": 12.0,
"key_activities": [
"Complete AWS Solutions Architect Associate certification",
"Build and deploy containerized applications",
"Set up basic Kubernetes cluster"
]
}},
"phase_2_core_development": {{
"duration": "3-6 months",
"focus_areas": ["Advanced Kubernetes", "CI/CD pipelines", "Monitoring systems"],
"expected_match_improvement": 15.0,
"key_activities": [
"Gain hands-on Kubernetes experience",
"Implement full CI/CD workflows",
"Learn infrastructure monitoring"
]
}},
"phase_3_mastery": {{
"duration": "6-12 months",
"focus_areas": ["Cloud architecture", "Team leadership", "System design"],
"expected_match_improvement": 8.0,
"key_activities": [
"Design scalable cloud architectures",
"Lead technical initiatives",
"Mentor junior developers"
]
}}
}},
"specific_recommendations": {{
"immediate_actions": [
"Enroll in Kubernetes fundamentals course this week",
"Set up personal AWS account for hands-on practice",
"Join relevant technical communities and forums"
],
"certification_priorities": [
{{
"certification": "Certified Kubernetes Administrator (CKA)",
"timeframe": "3 months",
"impact": "High - addresses critical gap",
"cost_estimate": "$300-500"
}},
{{
"certification": "AWS Solutions Architect Associate",
"timeframe": "2 months",
"impact": "Medium - strengthens cloud knowledge",
"cost_estimate": "$150"
}}
],
"project_ideas": [
"Build a microservices application with Kubernetes deployment",
"Create CI/CD pipeline using AWS services",
"Develop monitoring dashboard for cloud applications"
],
"learning_resources": {{
"free_resources": [
"Kubernetes official tutorials",
"AWS free tier hands-on labs",
"YouTube technical channels"
],
"paid_resources": [
"Linux Academy/A Cloud Guru courses",
"Pluralsight skill paths",
"Udemy specialized courses"
],
"books": [
"Kubernetes in Action",
"AWS Certified Solutions Architect Study Guide",
"Site Reliability Engineering"
]
}}
}},
"projected_outcomes": {{
"3_month_match_percentage": 75.0,
"6_month_match_percentage": 85.0,
"12_month_match_percentage": 90.0,
"confidence_level": "High - Based on candidate's strong foundation and learning ability",
"success_factors": [
"Strong programming background provides good foundation",
"Existing cloud knowledge accelerates learning",
"Demonstrated ability to learn new technologies"
],
"potential_challenges": [
"Time management while working full-time",
"Hands-on experience acquisition",
"Keeping up with rapidly evolving technologies"
]
}},
"success_metrics": {{
"short_term": [
"Complete 2 certifications within 3 months",
"Deploy 3 projects using new technologies",
"Contribute to open-source projects"
],
"long_term": [
"Lead technical implementation at current role",
"Speak at technical conferences or meetups",
"Mentor others in acquired skills"
]
}}
}}


## INPUT DATA

**CURRENT RESUME SKILLS:**
{resume_skills}

**JOB DESCRIPTION REQUIREMENTS:**
{jd_skills}

**CURRENT MATCH PERCENTAGE:** {match_percentage}%

## CRITICAL INSTRUCTIONS:
1. Focus on actionable, specific recommendations
2. Provide realistic timelines and expectations
3. Consider candidate's existing skills as foundation
4. Prioritize gaps with highest impact on match percentage
5. Include both free and paid learning resources
6. Account for practical experience acquisition
7. Provide measurable success metrics
8. Return ONLY the JSON object, no additional commentary
"""
