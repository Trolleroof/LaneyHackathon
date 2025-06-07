'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  DocumentTextIcon, 
  XMarkIcon, 
  CloudArrowUpIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ArrowPathIcon 
} from '@heroicons/react/24/outline';
import axios from 'axios';
import toast from 'react-hot-toast';

interface DocumentUploaderProps {
  onClose: () => void;
}

interface AnalysisResults {
  document_id: number;
  filename: string;
  analysis: {
    unfair_clauses: Array<{
      clause_text: string;
      issue: string;
      severity: 'high' | 'medium' | 'low';
      explanation: string;
      recommendation: string;
    }>;
    plain_english_summary: string;
    tenant_rights: Array<{
      title: string;
      description: string;
      importance: 'high' | 'medium' | 'low';
    }>;
    recommendations: string[];
    overall_score: number;
  };
}

export default function DocumentUploader({ onClose }: DocumentUploaderProps) {
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'processing' | 'complete' | 'error'>('idle');
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState<AnalysisResults | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isGeneratingLetter, setIsGeneratingLetter] = useState(false);
  const [generatedLetter, setGeneratedLetter] = useState<string | null>(null);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      toast.error('File size too large. Please upload a file smaller than 10MB.');
      return;
    }

    try {
      setUploadStatus('uploading');
      setProgress(20);
      
      const formData = new FormData();
      formData.append('file', file);
      
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 500);

      setUploadStatus('processing');
      
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await axios.post<AnalysisResults>(
        `${apiUrl}/api/upload-document`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          // Add auth header when implemented
          // headers: { Authorization: `Bearer ${token}` }
        }
      );

      clearInterval(progressInterval);
      setProgress(100);
      setResults(response.data);
      setUploadStatus('complete');
      toast.success('Document analyzed successfully!');

    } catch (err: any) {
      setUploadStatus('error');
      const errorMessage = err.response?.data?.detail || 'Failed to analyze document. Please try again.';
      setError(errorMessage);
      toast.error(errorMessage);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/*': ['.png', '.jpg', '.jpeg', '.tiff']
    },
    maxFiles: 1,
    disabled: uploadStatus !== 'idle',
    multiple: false,
    onDragEnter: () => {},
    onDragOver: () => {},
    onDragLeave: () => {},
  });

  const getSeverityColor = (severity: 'high' | 'medium' | 'low') => {
    switch (severity) {
      case 'high': return 'text-red-600 bg-red-50 border-red-200';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low': return 'text-blue-600 bg-blue-50 border-blue-200';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const handleGenerateLetter = async () => {
    if (!results) return;
    
    setIsGeneratingLetter(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      
      // Prepare the context from the analysis
      const letterContext = {
        unfair_clauses: results.analysis.unfair_clauses,
        overall_score: results.analysis.overall_score,
        filename: results.filename,
        recommendations: results.analysis.recommendations
      };
      
      const response = await axios.post(`${apiUrl}/api/generate-letter`, {
        letter_type: "general_concern",
        context: JSON.stringify(letterContext),
        tenant_info: {
          name: "Tenant", // Could be made dynamic
          address: "Your Address"
        },
        landlord_info: {
          name: "Landlord", // Could be extracted from lease
          address: "Landlord Address"
        },
        specific_issues: results.analysis.unfair_clauses.map(clause => clause.issue)
      });
      
      setGeneratedLetter(response.data.content);
      toast.success('Letter generated successfully!');
    } catch (err: any) {
      toast.error('Failed to generate letter. Please try again.');
      console.error('Letter generation error:', err);
    } finally {
      setIsGeneratingLetter(false);
    }
  };

  const handleDownloadReport = () => {
    if (!results) return;
    
    // Create a comprehensive report
    const reportContent = `
LEASE ANALYSIS REPORT
Generated: ${new Date().toLocaleDateString()}
Document: ${results.filename}

OVERALL FAIRNESS SCORE: ${results.analysis.overall_score}/100

SUMMARY:
${results.analysis.plain_english_summary}

PROBLEMATIC CLAUSES (${results.analysis.unfair_clauses.length}):
${results.analysis.unfair_clauses.map((clause, index) => `
${index + 1}. ${clause.issue} (${clause.severity.toUpperCase()} PRIORITY)
   Clause: "${clause.clause_text}"
   Explanation: ${clause.explanation}
   Recommended Action: ${clause.recommendation}
`).join('\n')}

YOUR RIGHTS & OBLIGATIONS:
${results.analysis.tenant_rights.map((right, index) => `
${index + 1}. ${right.title}
   ${right.description}
`).join('\n')}

RECOMMENDATIONS:
${results.analysis.recommendations.map((rec, index) => `${index + 1}. ${rec}`).join('\n')}

---
Generated by TenantRights AI Assistant
For educational purposes only. Consult with a legal professional for specific advice.
    `;
    
    // Create and download the file
    const blob = new Blob([reportContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `lease-analysis-${results.filename.replace(/\.[^/.]+$/, '')}-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    toast.success('Report downloaded successfully!');
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="bg-white rounded-2xl max-w-4xl max-h-[90vh] w-full overflow-hidden shadow-2xl"
          onClick={(e: React.MouseEvent) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <h2 className="text-2xl font-bold text-gray-900">Analyze Your Lease</h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <XMarkIcon className="h-6 w-6 text-gray-500" />
            </button>
          </div>

          <div className="p-6 overflow-y-auto max-h-[calc(90vh-80px)]">
            {/* Upload Area */}
            {uploadStatus === 'idle' && (
              <div
                {...getRootProps()}
                className={`
                  border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors
                  ${isDragActive 
                    ? 'border-blue-400 bg-blue-50' 
                    : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
                  }
                `}
              >
                <input {...getInputProps()} type="file" />
                <CloudArrowUpIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {isDragActive ? 'Drop your lease here' : 'Upload your lease document'}
                </h3>
                <p className="text-gray-600 mb-4">
                  Drag and drop your lease PDF or image, or click to browse
                </p>
                <p className="text-sm text-gray-500">
                  Supports PDF, PNG, JPG, TIFF • Max 10MB
                </p>
              </div>
            )}

            {/* Loading States */}
            {(uploadStatus === 'uploading' || uploadStatus === 'processing') && (
              <div className="text-center py-12">
                <div className="relative">
                  <ArrowPathIcon className="h-16 w-16 text-blue-600 mx-auto mb-4 animate-spin" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {uploadStatus === 'uploading' ? 'Uploading document...' : 'Analyzing lease...'}
                </h3>
                <p className="text-gray-600 mb-6">
                  {uploadStatus === 'uploading' 
                    ? 'Securely uploading your document' 
                    : 'Our AI is reading your lease and identifying key terms'
                  }
                </p>
                <div className="w-full bg-gray-200 rounded-full h-3 mb-4 max-w-md mx-auto">
                  <div 
                    className="bg-blue-600 h-3 rounded-full transition-all duration-300 ease-out"
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
                <p className="text-sm text-gray-500">{progress}% complete</p>
              </div>
            )}

            {/* Error State */}
            {uploadStatus === 'error' && (
              <div className="text-center py-12">
                <ExclamationTriangleIcon className="h-16 w-16 text-red-500 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Upload Failed</h3>
                <p className="text-red-600 mb-6">{error}</p>
                <button
                  onClick={() => {
                    setUploadStatus('idle');
                    setError(null);
                    setProgress(0);
                  }}
                  className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
                >
                  Try Again
                </button>
              </div>
            )}

            {/* Results */}
            {uploadStatus === 'complete' && results && (
              <div className="space-y-8">
                {/* Overall Score */}
                <div className="bg-gray-50 rounded-xl p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-bold text-gray-900">Lease Analysis Complete</h3>
                    <div className="text-right">
                      <div className={`text-3xl font-bold ${getScoreColor(results.analysis.overall_score)}`}>
                        {results.analysis.overall_score}/100
                      </div>
                      <p className="text-sm text-gray-600">Fairness Score</p>
                    </div>
                  </div>
                  <p className="text-gray-700">{results.analysis.plain_english_summary}</p>
                </div>

                {/* Unfair Clauses */}
                {results.analysis.unfair_clauses.length > 0 && (
                  <div>
                    <h4 className="text-lg font-bold text-gray-900 mb-4">
                      ⚠️ Problematic Clauses ({results.analysis.unfair_clauses.length})
                    </h4>
                    <div className="space-y-4">
                      {results.analysis.unfair_clauses.map((clause, index) => (
                        <div key={index} className={`border rounded-lg p-4 ${getSeverityColor(clause.severity)}`}>
                          <div className="flex items-start justify-between mb-2">
                            <span className={`text-xs font-medium px-2 py-1 rounded-full ${getSeverityColor(clause.severity)}`}>
                              {clause.severity.toUpperCase()} PRIORITY
                            </span>
                          </div>
                          <h5 className="font-semibold mb-2">{clause.issue}</h5>
                          <p className="text-sm mb-3 font-mono bg-white bg-opacity-50 p-2 rounded">
                            "{clause.clause_text}"
                          </p>
                          <p className="text-sm mb-2">{clause.explanation}</p>
                          <div className="bg-white bg-opacity-50 p-3 rounded text-sm">
                            <strong>Recommended Action:</strong> {clause.recommendation}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Tenant Rights */}
                {results.analysis.tenant_rights.length > 0 && (
                  <div>
                    <h4 className="text-lg font-bold text-gray-900 mb-4">
                      📋 Your Rights & Obligations
                    </h4>
                    <div className="grid gap-4">
                      {results.analysis.tenant_rights.map((right, index) => (
                        <div key={index} className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                          <h5 className="font-semibold text-blue-900 mb-2">{right.title}</h5>
                          <p className="text-blue-800 text-sm">{right.description}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Recommendations */}
                {results.analysis.recommendations.length > 0 && (
                  <div>
                    <h4 className="text-lg font-bold text-gray-900 mb-4">
                      💡 What You Should Do
                    </h4>
                    <div className="space-y-3">
                      {results.analysis.recommendations.map((rec, index) => (
                        <div key={index} className="flex items-start space-x-3">
                          <CheckCircleIcon className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
                          <p className="text-gray-700">{rec}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Generated Letter */}
                {generatedLetter && (
                  <div>
                    <h4 className="text-lg font-bold text-gray-900 mb-4">
                      📝 Generated Letter to Landlord
                    </h4>
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
                      <pre className="whitespace-pre-wrap text-sm text-gray-800 font-mono">
                        {generatedLetter}
                      </pre>
                      <div className="mt-4 flex gap-3">
                        <button
                          onClick={() => {
                            navigator.clipboard.writeText(generatedLetter);
                            toast.success('Letter copied to clipboard!');
                          }}
                          className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700 transition-colors"
                        >
                          Copy Letter
                        </button>
                        <button
                          onClick={() => {
                            const blob = new Blob([generatedLetter], { type: 'text/plain' });
                            const url = URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = `letter-to-landlord-${new Date().toISOString().split('T')[0]}.txt`;
                            document.body.appendChild(a);
                            a.click();
                            document.body.removeChild(a);
                            URL.revokeObjectURL(url);
                            toast.success('Letter downloaded!');
                          }}
                          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
                        >
                          Download Letter
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex flex-col sm:flex-row gap-4 pt-6 border-t border-gray-200">
                  {/* Debug info */}
                  <div className="text-xs text-gray-500 mb-2">
                    Debug: uploadStatus={uploadStatus}, results={results ? 'exists' : 'null'}, 
                    handleGenerateLetter={typeof handleGenerateLetter}, 
                    handleDownloadReport={typeof handleDownloadReport}
                  </div>
                  <button 
                    type="button"
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      console.log('Generate Letter button clicked!');
                      console.log('handleGenerateLetter function:', typeof handleGenerateLetter);
                      console.log('results:', results);
                      handleGenerateLetter();
                    }}
                    disabled={isGeneratingLetter}
                    className="flex-1 bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 cursor-pointer"
                  >
                    {isGeneratingLetter ? (
                      <>
                        <ArrowPathIcon className="h-5 w-5 animate-spin" />
                        Generating Letter...
                      </>
                    ) : (
                      '📝 Generate Letter to Landlord'
                    )}
                  </button>
                  <button 
                    type="button"
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      console.log('Download Report button clicked!');
                      console.log('handleDownloadReport function:', typeof handleDownloadReport);
                      console.log('results:', results);
                      handleDownloadReport();
                    }}
                    className="flex-1 bg-white text-blue-600 border-2 border-blue-600 px-6 py-3 rounded-lg font-medium hover:bg-blue-50 transition-colors cursor-pointer"
                  >
                    📄 Download Analysis Report
                  </button>
                </div>
              </div>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
} 