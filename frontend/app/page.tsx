'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  DocumentTextIcon, 
  ShieldCheckIcon, 
  ChatBubbleBottomCenterTextIcon,
  UserGroupIcon,
  ArrowRightIcon,
  CheckCircleIcon 
} from '@heroicons/react/24/outline';
import Link from 'next/link';
import DocumentUploader from '@/components/DocumentUploader';
import ChatBot from '@/components/ChatBot';

export default function HomePage() {
  const [showUploader, setShowUploader] = useState(false);

  const features = [
    {
      icon: DocumentTextIcon,
      title: 'Scan Your Lease',
      description: 'Upload your lease document and our AI will extract and analyze all the text automatically.',
      color: 'text-blue-600'
    },
    {
      icon: ShieldCheckIcon,
      title: 'Find Unfair Clauses',
      description: 'We identify potentially illegal or unfair terms that could be used against you.',
      color: 'text-red-600'
    },
    {
      icon: ChatBubbleBottomCenterTextIcon,
      title: 'Plain English Explanations',
      description: 'Complex legal jargon translated into simple language you can understand.',
      color: 'text-green-600'
    },
    {
      icon: UserGroupIcon,
      title: 'Generate Letters',
      description: 'Create professional letters to your landlord for repairs, deposits, and disputes.',
      color: 'text-purple-600'
    }
  ];

  const benefits = [
    'Free to use, no hidden fees',
    'Privacy-focused - your documents stay secure',
    'Designed for everyday renters',
    'No legal jargon or confusing terms',
    'Instant results in plain English',
    'Generate formal letters automatically'
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-3">
              <ShieldCheckIcon className="h-8 w-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">TenantRights AI</h1>
            </div>
            <nav className="hidden md:flex space-x-6">
              <Link href="/about" className="text-gray-600 hover:text-gray-900">About</Link>
              <Link href="/help" className="text-gray-600 hover:text-gray-900">Help</Link>
              <Link href="/contact" className="text-gray-600 hover:text-gray-900">Contact</Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
              Understand Your 
              <span className="text-blue-600"> Lease Rights</span>
            </h2>
            <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
              Our AI-powered assistant helps renters understand their lease agreements, 
              identify unfair clauses, and generate professional letters to landlords. 
              <span className="font-semibold text-gray-800"> Free, private, and designed for everyone.</span>
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.6 }}
            className="space-y-4 sm:space-y-0 sm:space-x-4 sm:flex sm:justify-center"
          >
            <button
              onClick={() => setShowUploader(true)}
              className="w-full sm:w-auto bg-blue-600 text-white px-8 py-4 rounded-lg font-semibold text-lg hover:bg-blue-700 transition-colors flex items-center justify-center space-x-2 shadow-lg hover:shadow-xl"
            >
              <DocumentTextIcon className="h-6 w-6" />
              <span>Upload Your Lease</span>
            </button>
            <Link
              href="/demo"
              className="w-full sm:w-auto bg-white text-blue-600 border-2 border-blue-600 px-8 py-4 rounded-lg font-semibold text-lg hover:bg-blue-50 transition-colors flex items-center justify-center space-x-2"
            >
              <span>See How It Works</span>
              <ArrowRightIcon className="h-5 w-5" />
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="bg-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h3 className="text-3xl font-bold text-gray-900 mb-4">How We Help You</h3>
            <p className="text-xl text-gray-600">Simple tools to understand and protect your rights as a renter</p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1, duration: 0.6 }}
                className="text-center p-6 rounded-lg border border-gray-200 hover:shadow-lg transition-shadow"
              >
                <feature.icon className={`h-12 w-12 mx-auto mb-4 ${feature.color}`} />
                <h4 className="text-xl font-semibold text-gray-900 mb-3">{feature.title}</h4>
                <p className="text-gray-600">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="bg-gray-50 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h3 className="text-3xl font-bold text-gray-900 mb-6">
                Built for Real Renters
              </h3>
              <p className="text-lg text-gray-600 mb-8">
                We know legal documents can be confusing and expensive legal help isn't always available. 
                That's why we created a tool that's accessible, easy to understand, and completely free.
              </p>
              <div className="space-y-4">
                {benefits.map((benefit, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1, duration: 0.6 }}
                    className="flex items-center space-x-3"
                  >
                    <CheckCircleIcon className="h-6 w-6 text-green-600 flex-shrink-0" />
                    <span className="text-gray-700">{benefit}</span>
                  </motion.div>
                ))}
              </div>
            </div>
            <div className="bg-white p-8 rounded-2xl shadow-lg">
              <div className="text-center">
                <div className="bg-blue-100 rounded-full p-4 w-20 h-20 mx-auto mb-6 flex items-center justify-center">
                  <ShieldCheckIcon className="h-10 w-10 text-blue-600" />
                </div>
                <h4 className="text-2xl font-bold text-gray-900 mb-3">Your Privacy Matters</h4>
                <p className="text-gray-600 mb-6">
                  We process your documents securely and don't store your personal information. 
                  Your lease details stay private and are automatically deleted after analysis.
                </p>
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <p className="text-green-800 font-medium">🔒 End-to-end encryption</p>
                  <p className="text-green-800 font-medium">🗑️ Auto-delete after 24 hours</p>
                  <p className="text-green-800 font-medium">🚫 No personal data stored</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-blue-600 py-16">
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <h3 className="text-3xl font-bold text-white mb-6">
            Ready to Understand Your Lease?
          </h3>
          <p className="text-xl text-blue-100 mb-8">
            Upload your lease document now and get instant analysis. It's free, secure, and takes less than 2 minutes.
          </p>
          <button
            onClick={() => setShowUploader(true)}
            className="bg-white text-blue-600 px-8 py-4 rounded-lg font-semibold text-lg hover:bg-gray-50 transition-colors inline-flex items-center space-x-2 shadow-lg"
          >
            <DocumentTextIcon className="h-6 w-6" />
            <span>Get Started Now</span>
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            <div className="col-span-2">
              <div className="flex items-center space-x-3 mb-4">
                <ShieldCheckIcon className="h-6 w-6" />
                <span className="text-xl font-bold">TenantRights AI</span>
              </div>
              <p className="text-gray-400 mb-4">
                Empowering renters with AI-powered lease analysis and tenant rights education.
              </p>
              <p className="text-sm text-gray-500">
                This tool provides general information and should not replace professional legal advice.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Resources</h4>
              <ul className="space-y-2 text-gray-400">
                <li><Link href="/help" className="hover:text-white">Help Center</Link></li>
                <li><Link href="/rights" className="hover:text-white">Know Your Rights</Link></li>
                <li><Link href="/templates" className="hover:text-white">Letter Templates</Link></li>
                <li><Link href="/contact" className="hover:text-white">Contact Support</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Legal</h4>
              <ul className="space-y-2 text-gray-400">
                <li><Link href="/privacy" className="hover:text-white">Privacy Policy</Link></li>
                <li><Link href="/terms" className="hover:text-white">Terms of Service</Link></li>
                <li><Link href="/disclaimer" className="hover:text-white">Legal Disclaimer</Link></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
            <p>&copy; 2024 TenantRights AI. Made with ❤️ for renters everywhere.</p>
          </div>
        </div>
      </footer>

      {/* Document Uploader Modal */}
      {showUploader && (
        <DocumentUploader onClose={() => setShowUploader(false)} />
      )}

      {/* Floating ChatBot */}
      <ChatBot />
    </div>
  );
} 