'use client';

import { useState } from 'react';
import axios from 'axios';
import UploadSection from '@/components/UploadSection';
import ResultsView from '@/components/ResultsView';
import { MatchResponse } from '@/types';

export default function Home() {
  const [results, setResults] = useState<MatchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');

  const handleSubmit = async (jdText: string, files: File[]) => {
    setLoading(true);
    setError('');
    setResults(null);

    try {
      // Create FormData for multipart upload
      const formData = new FormData();
      formData.append('jd_text', jdText);
      
      files.forEach((file) => {
        formData.append('files', file);
      });

      // Get API URL from environment or use default
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

      // Make API request
      const response = await axios.post<MatchResponse>(
        `${apiUrl}/api/match`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 300000, // 5 minutes timeout for large batches
        }
      );

      setResults(response.data);
    } catch (err: unknown) {
      console.error('Error submitting match request:', err);
      
      if (axios.isAxiosError(err)) {
        const message = err.response?.data?.detail || err.message || 'Failed to process resumes';
        setError(message);
      } else {
        setError('An unexpected error occurred');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <header className="mb-8 text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            AI Resume Matcher
          </h1>
          <p className="text-gray-600 text-lg">
            Enterprise-grade multi-agent system for intelligent resume matching
          </p>
        </header>

        {/* Error Display */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-lg">
            <p className="font-semibold">Error:</p>
            <p>{error}</p>
          </div>
        )}

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left: Upload Section */}
          <div>
            <UploadSection onSubmit={handleSubmit} loading={loading} />
          </div>

          {/* Right: Results View */}
          <div>
            <ResultsView results={results} />
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-12 text-center text-gray-600 text-sm">
          <p>
            Powered by LangGraph, Gemini 2.5, OpenRouter, Pinecone & MongoDB
          </p>
        </footer>
      </div>
    </div>
  );
}
