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

interface CommonQuestion {
  category: string;
  questions: string[];
}

export default function ChatBot() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [commonQuestions, setCommonQuestions] = useState<CommonQuestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load common questions when component mounts
  useEffect(() => {
    if (isOpen && commonQuestions.length === 0) {
      loadCommonQuestions();
    }
  }, [isOpen]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadCommonQuestions = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await axios.get(`${apiUrl}/api/chat/common-questions`);
      setCommonQuestions(response.data.categories);
    } catch (error) {
      console.error('Failed to load common questions:', error);
    }
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
    setShowSuggestions(false);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      
      const response = await axios.post<ChatResponse>(`${apiUrl}/api/chat`, {
        message: message,
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
    // Simple formatting for better readability
    return content.split('\n').map((line, index) => (
      <div key={index} className={index > 0 ? 'mt-2' : ''}>
        {line}
      </div>
    ));
  };

  return (
    <>
      {/* Chat Toggle Button */}
      <motion.button
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={() => setIsOpen(true)}
        className={`fixed bottom-6 right-6 bg-blue-600 text-white p-4 rounded-full shadow-lg hover:bg-blue-700 transition-colors z-40 ${isOpen ? 'hidden' : 'block'}`}
      >
        <ChatBubbleBottomCenterTextIcon className="h-6 w-6" />
      </motion.button>

      {/* Chat Window */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: 20 }}
            className="fixed bottom-6 right-6 w-96 h-[32rem] bg-white rounded-2xl shadow-2xl border border-gray-200 flex flex-col z-50 overflow-hidden"
          >
            {/* Header */}
            <div className="bg-blue-600 text-white p-4 flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <ChatBubbleBottomCenterTextIcon className="h-6 w-6" />
                <div>
                  <h3 className="font-semibold">TenantRights Assistant</h3>
                  <p className="text-blue-100 text-sm">Ask me about your tenant rights</p>
                </div>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 hover:bg-blue-700 rounded-lg transition-colors"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 && showSuggestions && (
                <div className="space-y-4">
                                     <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                     <p className="text-black text-sm font-medium mb-2">
                       👋 Hi! I'm your tenant rights assistant. I can help you with:
                     </p>
                     <ul className="text-black text-sm space-y-1">
                      <li>• Understanding lease terms</li>
                      <li>• Tenant rights and responsibilities</li>
                      <li>• Repair and maintenance issues</li>
                      <li>• Rent and payment questions</li>
                      <li>• Security deposit concerns</li>
                    </ul>
                  </div>

                  {/* Common Questions */}
                  {commonQuestions.slice(0, 2).map((category, categoryIndex) => (
                                         <div key={categoryIndex} className="space-y-2">
                       <p className="text-sm font-medium text-black">{category.category}:</p>
                      {category.questions.slice(0, 2).map((question, questionIndex) => (
                                                 <button
                           key={questionIndex}
                           onClick={() => handleQuestionClick(question)}
                           className="w-full text-left bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg p-2 text-sm transition-colors text-black"
                         >
                          {question}
                        </button>
                      ))}
                    </div>
                  ))}
                </div>
              )}

              {/* Chat Messages */}
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] p-3 rounded-lg ${
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
                       <span className="text-sm">Thinking...</span>
                     </div>
                   </div>
                 </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input Form */}
            <div className="border-t border-gray-200 p-4">
              <form onSubmit={handleSubmit} className="flex space-x-2">
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder="Ask about your tenant rights..."
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
                This is AI-generated information. Consult a lawyer for legal advice.
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
} 