'use client';

import { ResultsViewProps, ResumeMatch } from '@/types';

export default function ResultsView({ results }: ResultsViewProps) {
  if (!results) {
    return (
      <div className="bg-gray-50 rounded-lg shadow-md p-6 flex items-center justify-center min-h-[400px]">
        <p className="text-gray-500 text-lg">
          No results yet. Upload a job description and resumes to get started.
        </p>
      </div>
    );
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'bg-green-50 text-green-600 border-green-200';
    if (score >= 65) return 'bg-yellow-50 text-yellow-600 border-yellow-200';
    return 'bg-red-50 text-red-600 border-red-200';
  };

  const getScoreBadgeColor = (score: number) => {
    if (score >= 80) return 'bg-green-100 text-green-800';
    if (score >= 65) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">Match Results</h2>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
          <p className="text-sm text-blue-600 font-medium">Total Resumes</p>
          <p className="text-3xl font-bold text-blue-800">{results.total_resumes}</p>
        </div>
        
        <div className="bg-green-50 rounded-lg p-4 border border-green-200">
          <p className="text-sm text-green-600 font-medium">High Matches (≥80%)</p>
          <p className="text-3xl font-bold text-green-800">{results.high_matches}</p>
        </div>
        
        <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
          <p className="text-sm text-yellow-600 font-medium">Potential (65-79%)</p>
          <p className="text-3xl font-bold text-yellow-800">{results.potential_matches}</p>
        </div>
      </div>

      {/* Match Cards */}
      <div className="space-y-4 max-h-[600px] overflow-y-auto">
        {results.matches.map((match: ResumeMatch, index: number) => (
          <div
            key={match.resume_id}
            className={`rounded-lg border-2 p-4 ${getScoreColor(match.match_score)}`}
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="text-lg font-bold">
                  {match.candidate_name || `Candidate ${index + 1}`}
                </h3>
                <p className="text-sm text-gray-600">{match.resume_id}</p>
              </div>
              <div className={`px-4 py-2 rounded-full font-bold text-lg ${getScoreBadgeColor(match.match_score)}`}>
                {match.match_score}%
              </div>
            </div>

            {/* Score Breakdown */}
            <div className="grid grid-cols-3 gap-3 mb-3">
              <div className="bg-white bg-opacity-60 rounded p-2">
                <p className="text-xs font-medium text-gray-600">Skills</p>
                <p className="text-lg font-bold">{match.skill_match_score}%</p>
              </div>
              <div className="bg-white bg-opacity-60 rounded p-2">
                <p className="text-xs font-medium text-gray-600">Experience</p>
                <p className="text-lg font-bold">{match.experience_match_score}%</p>
              </div>
              <div className="bg-white bg-opacity-60 rounded p-2">
                <p className="text-xs font-medium text-gray-600">Role Fit</p>
                <p className="text-lg font-bold">{match.role_match_score}%</p>
              </div>
            </div>

            {/* Matched Skills */}
            {match.matched_skills.length > 0 && (
              <div className="mb-3">
                <p className="text-sm font-semibold mb-2">Matched Skills:</p>
                <div className="flex flex-wrap gap-2">
                  {match.matched_skills.map((skill, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-medium"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Missing Skills */}
            {match.missing_skills.length > 0 && (
              <div className="mb-3">
                <p className="text-sm font-semibold mb-2">Missing Skills:</p>
                <div className="flex flex-wrap gap-2">
                  {match.missing_skills.map((skill, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs font-medium"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Skill Gap Recommendations */}
            {match.skill_gaps && match.skill_gaps.length > 0 && (
              <div className="mb-3 bg-white bg-opacity-80 rounded-lg p-3">
                <p className="text-sm font-semibold mb-2">Skill Development Recommendations:</p>
                <div className="space-y-2">
                  {match.skill_gaps.map((gap, idx) => (
                    <div key={idx} className="border-l-4 border-blue-500 pl-3">
                      <p className="font-semibold text-sm">
                        {gap.missing_skill}
                        <span className={`ml-2 text-xs px-2 py-0.5 rounded ${
                          gap.importance === 'high' ? 'bg-red-100 text-red-800' :
                          gap.importance === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {gap.importance.toUpperCase()}
                        </span>
                      </p>
                      <p className="text-xs text-gray-700 mt-1">{gap.reason}</p>
                      <p className="text-xs text-gray-600 mt-1">
                        <span className="font-medium">Learning Path:</span> {gap.learning_path}
                      </p>
                      <p className="text-xs text-gray-600">
                        <span className="font-medium">Time:</span> {gap.estimated_time}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recommendation */}
            <div className="bg-white bg-opacity-80 rounded p-3">
              <p className="text-sm font-semibold mb-1">Recommendation:</p>
              <p className="text-sm">{match.recommendation}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
