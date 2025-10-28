/**
 * TypeScript type definitions for AI Resume Matcher.
 */

export interface SkillGap {
  missing_skill: string;
  importance: 'high' | 'medium' | 'low';
  reason: string;
  learning_path: string;
  estimated_time: string;
}

export interface ResumeMatch {
  resume_id: string;
  candidate_name: string | null;
  match_score: number;
  skill_match_score: number;
  experience_match_score: number;
  role_match_score: number;
  matched_skills: string[];
  missing_skills: string[];
  skill_gaps?: SkillGap[];
  recommendation: string;
}

export interface MatchResponse {
  matches: ResumeMatch[];
  total_resumes: number;
  high_matches: number;
  potential_matches: number;
}

export interface UploadSectionProps {
  onSubmit: (jdText: string, files: File[]) => Promise<void>;
  onDatabaseSearch: (jdText: string, minMatchScore: number) => Promise<void>;
  onStoreResumes: (files: File[]) => Promise<void>;
  loading: boolean;
  mode: 'upload' | 'search';
  onModeChange: (mode: 'upload' | 'search') => void;
}

export interface ResultsViewProps {
  results: MatchResponse | null;
  mode: 'upload' | 'search';
}

export interface StorageResponse {
  success: boolean;
  total_files: number;
  stored_count: number;
  failed_count: number;
  message: string;
}
