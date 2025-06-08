'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ChatBubbleBottomCenterTextIcon,
  XMarkIcon,
  PaperAirplaneIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import axios from 'axios';
import toast from 'react-hot-toast';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: Date;
}

interface ChatResponse {
  response: string;
  suggested_questions: string[];
  references: string[];
  chat_id?: number;
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

interface AnalysisChatBotProps {
  analysisResults: AnalysisResults;
  translations: {
    askQuestions: string;
    issuesFound: string;
  };
}

export default function AnalysisChatBot({ analysisResults, translations }: AnalysisChatBotProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Generate contextual questions based on analysis
  const getContextualQuestions = () => {
    const questions = [];
    
    if (analysisResults.analysis.unfair_clauses.length > 0) {
      questions.push(`What should I do about the ${analysisResults.analysis.unfair_clauses.length} problematic clauses in my lease?`);
      
      const highSeverityClauses = analysisResults.analysis.unfair_clauses.filter(c => c.severity === 'high');
      if (highSeverityClauses.length > 0) {
        questions.push(`How serious are the high-priority issues in my lease?`);
      }
    }

    if (analysisResults.analysis.overall_score < 70) {
      questions.push(`My lease scored ${analysisResults.analysis.overall_score}/100. What does this mean?`);
    }

    questions.push(`Can you explain the most important issue in my lease?`);
    questions.push(`What's my next step after reviewing this analysis?`);
    questions.push(`Are these lease terms legal in my area?`);

    return questions.slice(0, 4); // Return top 4 questions
  };

  const sendMessage = async (message: string) => {
    if (!message.trim()) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: message,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      
      // Prepare detailed context about the lease analysis
      const leaseContext = {
        filename: analysisResults.filename,
        overall_score: analysisResults.analysis.overall_score,
        problematic_clauses: analysisResults.analysis.unfair_clauses.map(clause => ({
          issue: clause.issue,
          severity: clause.severity,
          clause_text: clause.clause_text,
          explanation: clause.explanation,
          recommendation: clause.recommendation
        })),
        tenant_rights: analysisResults.analysis.tenant_rights,
        recommendations: analysisResults.analysis.recommendations,
        summary: analysisResults.analysis.plain_english_summary
      };

      const response = await axios.post<ChatResponse>(`${apiUrl}/api/chat`, {
        message: `${message}\n\nLEASE CONTEXT: ${JSON.stringify(leaseContext)}`,
        document_id: analysisResults.document_id,
        chat_history: messages.slice(-5) // Send last 5 messages for context
      });

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);

    } catch (error: any) {
      console.error('Chat error:', error);
      const errorMessage = error.response?.status === 401 
        ? "Please log in to use the chat feature."
        : "Sorry, I'm having trouble responding right now. Please try again.";
      
      const errorResponse: ChatMessage = {
        role: 'assistant',
        content: errorMessage,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorResponse]);
      toast.error('Failed to send message');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(inputMessage);
  };

  const handleQuestionClick = (question: string) => {
    sendMessage(question);
  };

  const formatMessage = (content: string) => {
    return content.split('\n').map((line, index) => (
      <div key={index} className={index > 0 ? 'mt-2' : ''}>
        {line}
      </div>
    ));
  };

  return (
    <div className="border-t border-gray-200 bg-gray-50">
      {/* Chat Toggle */}
      <div className="p-4">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="w-full flex items-center justify-center space-x-2 bg-blue-600 text-white px-4 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
        >
          <ChatBubbleBottomCenterTextIcon className="h-5 w-5" />
          <span>{translations.askQuestions}</span>
          {isOpen ? (
            <XMarkIcon className="h-4 w-4" />
          ) : (
            <span className="text-blue-200 text-sm ml-2">({analysisResults.analysis.unfair_clauses.length} {translations.issuesFound})</span>
          )}
        </button>
      </div>

      {/* Chat Interface */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-gray-200"
          >
            {/* Chat Header */}
            <div className="bg-blue-600 text-white p-4">
              <div className="flex items-center space-x-3">
                <ChatBubbleBottomCenterTextIcon className="h-5 w-5" />
                <div>
                  <h4 className="font-semibold">Chat About Your Lease Analysis</h4>
                  <p className="text-blue-100 text-sm">
                    Ask questions about your {analysisResults.filename} analysis
                  </p>
                </div>
              </div>
            </div>

            {/* Messages Area */}
            <div className="h-80 overflow-y-auto p-4 space-y-4 bg-white">
              {/* Initial Context Message */}
              {messages.length === 0 && (
                <div className="space-y-4">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <p className="text-black text-sm font-medium mb-3">
                      🏠 I'm here to help with your lease analysis! Your lease scored <span className="font-bold">{analysisResults.analysis.overall_score}/100</span> with <span className="font-bold">{analysisResults.analysis.unfair_clauses.length} problematic clauses</span> identified.
                    </p>
                    <p className="text-black text-sm mb-3">Ask me anything about:</p>
                    <ul className="text-black text-sm space-y-1 list-disc list-inside">
                      <li>Specific clauses and their issues</li>
                      <li>Your rights and next steps</li>
                      <li>How to address problems with your landlord</li>
                      <li>Legal options and resources</li>
                    </ul>
                  </div>

                  {/* Contextual Questions */}
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-black">Quick questions to get started:</p>
                    {getContextualQuestions().map((question, index) => (
                      <button
                        key={index}
                        onClick={() => handleQuestionClick(question)}
                        className="w-full text-left bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg p-3 text-sm transition-colors text-black"
                      >
                        {question}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Chat Messages */}
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[85%] p-3 rounded-lg ${
                      message.role === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-black'
                    }`}
                  >
                    <div className="text-sm">
                      {formatMessage(message.content)}
                    </div>
                    {message.timestamp && (
                      <div className={`text-xs mt-1 ${
                        message.role === 'user' ? 'text-blue-100' : 'text-black'
                      }`}>
                        {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {/* Loading Indicator */}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 text-black p-3 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <ArrowPathIcon className="h-4 w-4 animate-spin" />
                      <span className="text-sm">Analyzing your lease context...</span>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input Form */}
            <div className="border-t border-gray-200 p-4 bg-gray-50">
              <form onSubmit={handleSubmit} className="flex space-x-2">
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder="Ask about your specific lease issues..."
                  className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-black placeholder-gray-500"
                  disabled={isLoading}
                />
                <button
                  type="submit"
                  disabled={isLoading || !inputMessage.trim()}
                  className="bg-blue-600 text-white p-2 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <PaperAirplaneIcon className="h-4 w-4" />
                </button>
              </form>
              <p className="text-xs text-black mt-2 text-center">
                Responses are based on your lease analysis. Consult a lawyer for legal advice.
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
} 