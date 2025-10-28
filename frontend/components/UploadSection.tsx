'use client';

import { useState } from 'react';
import { UploadSectionProps } from '@/types';

export default function UploadSection({ 
  onSubmit, 
  onDatabaseSearch,
  onStoreResumes,
  loading,
  mode,
  onModeChange
}: UploadSectionProps) {
  const [jdText, setJdText] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [minMatchScore, setMinMatchScore] = useState(80);
  const [error, setError] = useState<string>('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    
    // Validate files
    const pdfFiles = files.filter(file => file.name.endsWith('.pdf'));
    
    if (pdfFiles.length !== files.length) {
      setError('Only PDF files are allowed');
      return;
    }
    
    const maxFiles = mode === 'upload' ? 50 : 100;
    if (pdfFiles.length > maxFiles) {
      setError(`Maximum ${maxFiles} files allowed`);
      return;
    }
    
    setSelectedFiles(pdfFiles);
    setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (mode === 'upload') {
      // Validate inputs for upload mode
      if (!jdText.trim()) {
        setError('Please enter a job description');
        return;
      }
      
      if (selectedFiles.length === 0) {
        setError('Please select at least one resume file');
        return;
      }
      
      setError('');
      await onSubmit(jdText, selectedFiles);
    } else {
      // Validate inputs for search mode
      if (!jdText.trim()) {
        setError('Please enter a job description');
        return;
      }
      
      setError('');
      await onDatabaseSearch(jdText, minMatchScore);
    }
  };

  const handleStoreResumes = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (selectedFiles.length === 0) {
      setError('Please select at least one resume file to store');
      return;
    }
    
    setError('');
    await onStoreResumes(selectedFiles);
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">
        {mode === 'upload' ? 'Upload & Match Resumes' : 'Search Stored Resumes'}
      </h2>
      
      {/* Mode Toggle */}
      <div className="mb-6 flex gap-2">
        <button
          onClick={() => onModeChange('upload')}
          className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors ${
            mode === 'upload'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
          disabled={loading}
        >
          Upload Mode
        </button>
        <button
          onClick={() => onModeChange('search')}
          className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors ${
            mode === 'search'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
          disabled={loading}
        >
          Search Mode
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Job Description Input */}
        <div>
          <label
            htmlFor="jd-text"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            Job Description
          </label>
          <textarea
            id="jd-text"
            value={jdText}
            onChange={(e) => setJdText(e.target.value)}
            className="w-full h-48 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            placeholder="Paste the job description here..."
            disabled={loading}
            aria-label="Job Description Text"
          />
        </div>

        {/* Upload Mode - File Upload */}
        {mode === 'upload' && (
          <div>
            <label
              htmlFor="resume-files"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Resume Files (PDF) - Max 50
            </label>
            <input
              id="resume-files"
              type="file"
              accept=".pdf"
              multiple
              onChange={handleFileChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              disabled={loading}
              aria-label="Resume PDF Files"
            />
            
            {selectedFiles.length > 0 && (
              <p className="mt-2 text-sm text-gray-600">
                {selectedFiles.length} file{selectedFiles.length !== 1 ? 's' : ''} selected
              </p>
            )}
          </div>
        )}

        {/* Search Mode - Match Score Threshold */}
        {mode === 'search' && (
          <div>
            <label
              htmlFor="min-match-score"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Minimum Match Score: {minMatchScore}%
            </label>
            <input
              id="min-match-score"
              type="range"
              min="0"
              max="100"
              step="5"
              value={minMatchScore}
              onChange={(e) => setMinMatchScore(parseInt(e.target.value))}
              className="w-full"
              disabled={loading}
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>0%</span>
              <span>50%</span>
              <span>100%</span>
            </div>
            <p className="mt-2 text-sm text-gray-600">
              Default: 80% (recommended for high-quality matches)
            </p>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 text-white font-semibold py-3 px-6 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors duration-200"
          aria-label={mode === 'upload' ? 'Match Resumes' : 'Search Database'}
        >
          {loading 
            ? 'Processing...' 
            : mode === 'upload' 
              ? 'Match Resumes' 
              : 'Search Database'
          }
        </button>
      </form>

      {/* Store Resumes Section (Always visible) */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <h3 className="text-lg font-semibold text-gray-800 mb-3">
          Store Resumes for Future Searches
        </h3>
        <form onSubmit={handleStoreResumes} className="space-y-4">
          <div>
            <input
              type="file"
              accept=".pdf"
              multiple
              onChange={handleFileChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-green-50 file:text-green-700 hover:file:bg-green-100"
              disabled={loading}
            />
            {selectedFiles.length > 0 && (
              <p className="mt-2 text-sm text-gray-600">
                {selectedFiles.length} file{selectedFiles.length !== 1 ? 's' : ''} selected
              </p>
            )}
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-green-600 text-white font-semibold py-2 px-6 rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors duration-200"
          >
            {loading ? 'Storing...' : 'Store in Database'}
          </button>
        </form>
      </div>

      {/* Loading Indicator */}
      {loading && (
        <div className="mt-4 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">
            {mode === 'upload' ? 'Analyzing resumes...' : 'Searching database...'}
          </span>
        </div>
      )}
    </div>
  );
}
