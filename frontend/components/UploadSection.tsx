'use client';

import { useState } from 'react';
import { UploadSectionProps } from '@/types';

export default function UploadSection({ onSubmit, loading }: UploadSectionProps) {
  const [jdText, setJdText] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [error, setError] = useState<string>('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    
    // Validate files
    const pdfFiles = files.filter(file => file.name.endsWith('.pdf'));
    
    if (pdfFiles.length !== files.length) {
      setError('Only PDF files are allowed');
      return;
    }
    
    if (pdfFiles.length > 50) {
      setError('Maximum 50 files allowed');
      return;
    }
    
    setSelectedFiles(pdfFiles);
    setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate inputs
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
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">
        Upload Job Description & Resumes
      </h2>
      
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
            className="w-full h-64 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            placeholder="Paste the job description here..."
            disabled={loading}
            aria-label="Job Description Text"
          />
        </div>

        {/* File Upload */}
        <div>
          <label
            htmlFor="resume-files"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            Resume Files (PDF)
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
          aria-label="Submit for Matching"
        >
          {loading ? 'Processing...' : 'Match Resumes'}
        </button>
      </form>

      {/* Loading Indicator */}
      {loading && (
        <div className="mt-4 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">Analyzing resumes...</span>
        </div>
      )}
    </div>
  );
}
