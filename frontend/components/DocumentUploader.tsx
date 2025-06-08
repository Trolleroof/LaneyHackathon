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
  ArrowPathIcon,
  LanguageIcon
} from '@heroicons/react/24/outline';
import axios from 'axios';
import toast from 'react-hot-toast';
import AnalysisChatBot from './AnalysisChatBot';
import { jsPDF } from 'jspdf';

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

const SUPPORTED_LANGUAGES = [
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
  { code: 'it', name: 'Italiano', flag: '🇮🇹' },
  { code: 'pt', name: 'Português', flag: '🇵🇹' },
  { code: 'zh', name: '中文', flag: '🇨🇳' },
  { code: 'ja', name: '日本語', flag: '🇯🇵' },
  { code: 'ko', name: '한국어', flag: '🇰🇷' },
  { code: 'ar', name: 'العربية', flag: '🇸🇦' }
];

export default function DocumentUploader({ onClose }: DocumentUploaderProps) {
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'processing' | 'complete' | 'error'>('idle');
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState<AnalysisResults | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isGeneratingLetter, setIsGeneratingLetter] = useState(false);
  const [generatedLetter, setGeneratedLetter] = useState<string | null>(null);
  const [selectedLanguage, setSelectedLanguage] = useState('en');

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
      formData.append('language', selectedLanguage);
      
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
  }, [selectedLanguage]);

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
        language: selectedLanguage,
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
    
    try {
      // Create a new PDF document
      const pdf = new jsPDF();
      const pageWidth = pdf.internal.pageSize.getWidth();
      const pageHeight = pdf.internal.pageSize.getHeight();
      const margin = 20;
      const lineHeight = 6;
      let yPosition = margin;

      // Helper function to clean text and remove problematic characters
      const cleanText = (text: string): string => {
        return text
          .replace(/[^\x00-\x7F]/g, '') // Remove non-ASCII characters
          .replace(/Ø=ÜÈ/g, '') // Remove specific encoding artifacts
          .replace(/Ø=Üþ/g, '') // Remove specific encoding artifacts
          .replace(/Ø=Ü°/g, '') // Remove specific encoding artifacts
          .replace(/Ø<ßa/g, '') // Remove specific encoding artifacts
          .trim();
      };

      // Helper function to add text with word wrapping
      const addText = (text: string, fontSize: number = 10, isBold: boolean = false) => {
        const cleanedText = cleanText(text);
        pdf.setFontSize(fontSize);
        if (isBold) {
          pdf.setFont('helvetica', 'bold');
        } else {
          pdf.setFont('helvetica', 'normal');
        }
        
        const lines = pdf.splitTextToSize(cleanedText, pageWidth - 2 * margin);
        
        // Check if we need a new page
        if (yPosition + (lines.length * lineHeight) > pageHeight - margin) {
          pdf.addPage();
          yPosition = margin;
        }
        
        pdf.text(lines, margin, yPosition);
        yPosition += lines.length * lineHeight + 3;
      };

      // Helper function to add a section break
      const addSectionBreak = () => {
        yPosition += 5;
      };

      // Title
      addText('LEASE ANALYSIS REPORT', 18, true);
      addSectionBreak();

      // Document info
      addText(`Generated: ${new Date().toLocaleDateString()}`, 10);
      addText(`Document: ${results.filename}`, 10);
      const selectedLang = SUPPORTED_LANGUAGES.find(lang => lang.code === selectedLanguage);
      addText(`Language: ${selectedLang?.flag} ${selectedLang?.name}`, 10);
      addSectionBreak();

      // Overall Score
      const scoreColor: [number, number, number] = results.analysis.overall_score >= 80 ? [0, 128, 0] : 
                        results.analysis.overall_score >= 60 ? [255, 165, 0] : [255, 0, 0];
      pdf.setTextColor(scoreColor[0], scoreColor[1], scoreColor[2]);
      addText(`OVERALL FAIRNESS SCORE: ${results.analysis.overall_score}/100`, 14, true);
      pdf.setTextColor(0, 0, 0); // Reset to black
      addSectionBreak();

      // Summary
      addText('SUMMARY:', 12, true);
      addText(results.analysis.plain_english_summary, 10);
      addSectionBreak();

      // Problematic Clauses
      if (results.analysis.unfair_clauses.length > 0) {
        addText(`PROBLEMATIC CLAUSES (${results.analysis.unfair_clauses.length}):`, 12, true);
        
        results.analysis.unfair_clauses.forEach((clause, index) => {
          // Set color based on severity
          const severityColor: [number, number, number] = clause.severity === 'high' ? [255, 0, 0] : 
                               clause.severity === 'medium' ? [255, 165, 0] : [0, 0, 255];
          
          pdf.setTextColor(severityColor[0], severityColor[1], severityColor[2]);
          addText(`${index + 1}. ${clause.issue} (${clause.severity.toUpperCase()} PRIORITY)`, 11, true);
          pdf.setTextColor(0, 0, 0);
          
          addText(`Clause: "${clause.clause_text}"`, 9);
          addText(`Explanation: ${clause.explanation}`, 9);
          addText(`Recommended Action: ${clause.recommendation}`, 9);
          addSectionBreak();
        });
      }

      // Tenant Rights
      if (results.analysis.tenant_rights.length > 0) {
        addText('YOUR RIGHTS & OBLIGATIONS:', 12, true);
        results.analysis.tenant_rights.forEach((right, index) => {
          addText(`${index + 1}. ${right.title}`, 10, true);
          addText(`   ${right.description}`, 9);
        });
        addSectionBreak();
      }

      // Recommendations
      if (results.analysis.recommendations.length > 0) {
        addText('RECOMMENDATIONS:', 12, true);
        results.analysis.recommendations.forEach((rec, index) => {
          addText(`${index + 1}. ${rec}`, 10);
        });
        addSectionBreak();
      }

      // Footer
      pdf.setTextColor(128, 128, 128);
      addText('Generated by TenantRights AI Assistant', 8);
      addText('For educational purposes only. Consult with a legal professional for specific advice.', 8);

      // Save the PDF
      const langSuffix = selectedLanguage !== 'en' ? `-${selectedLanguage}` : '';
      const filename = `lease-analysis-${results.filename.replace(/\.[^/.]+$/, '')}${langSuffix}-${new Date().toISOString().split('T')[0]}.pdf`;
      pdf.save(filename);
      
      toast.success('PDF report downloaded successfully!');
    } catch (error) {
      console.error('Error generating PDF:', error);
      toast.error('Failed to generate PDF. Falling back to text format.');
      
      // Fallback to text format if PDF fails
      const reportContent = `
LEASE ANALYSIS REPORT
Generated: ${new Date().toLocaleDateString()}
Document: ${results.filename}
Language: ${SUPPORTED_LANGUAGES.find(lang => lang.code === selectedLanguage)?.name}

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
      
      const blob = new Blob([reportContent], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const langSuffix = selectedLanguage !== 'en' ? `-${selectedLanguage}` : '';
      a.download = `lease-analysis-${results.filename.replace(/\.[^/.]+$/, '')}${langSuffix}-${new Date().toISOString().split('T')[0]}.txt`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
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
              <>
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

                {/* Language Selection */}
                <div className="mt-6 bg-gray-50 rounded-xl p-4">
                  <div className="flex items-center gap-3 mb-3">
                    <LanguageIcon className="h-5 w-5 text-gray-600" />
                    <h4 className="text-sm font-medium text-gray-900">Analysis Language (Optional)</h4>
                  </div>
                  <select
                    value={selectedLanguage}
                    onChange={(e) => setSelectedLanguage(e.target.value)}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                  >
                    {SUPPORTED_LANGUAGES.map((lang) => (
                      <option key={lang.code} value={lang.code}>
                        {lang.flag} {lang.name}
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-500 mt-2">
                    All analysis results, reports, and letters will be generated in your selected language.
                  </p>
                </div>
              </>
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
                <div className="flex gap-4 pt-6 border-t border-gray-200">
                  <button 
                    type="button"
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      handleGenerateLetter();
                    }}
                    disabled={isGeneratingLetter}
                    className="w-1/2 bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
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
                      handleDownloadReport();
                    }}
                    className="w-1/2 bg-white text-blue-600 border-2 border-blue-600 px-6 py-3 rounded-lg font-medium hover:bg-blue-50 transition-colors"
                  >
                    📄 Download PDF Report
                  </button>
                </div>

                {/* Contextual Chatbot */}
                <AnalysisChatBot analysisResults={results} />
              </div>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
} 