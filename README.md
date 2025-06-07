# TenantRights AI Assistant

An AI-powered assistant designed to empower renters—especially in underserved communities—by making lease agreements understandable and actionable.

## Features

- 📄 **Document Scanning**: OCR processing of lease agreements
- 🤖 **AI Analysis**: Fine-tuned legal language model for clause interpretation
- ⚠️ **Unfair Clause Detection**: Automatically highlights problematic terms
- 📝 **Plain English Explanations**: Translates legal jargon into accessible language
- ✍️ **Letter Generation**: Auto-generates formal requests and dispute letters
- 🔒 **Privacy-First**: Local processing and encrypted storage
- 📱 **Mobile-Friendly**: Progressive Web App for accessibility

## Tech Stack

### Frontend
- Next.js 14 with TypeScript
- Tailwind CSS for styling
- Progressive Web App (PWA)
- React Hook Form for file uploads

### Backend
- Python FastAPI
- PostgreSQL database
- Redis for caching
- ChromaDB for vector storage

### AI/ML
- Google Gemini Flash 2.0 (fast and cost-effective)
- Tesseract OCR for document processing
- ChromaDB for vector storage
- Sentence Transformers for embeddings

## Project Structure

```
tenant-rights-ai/
├── frontend/                 # Next.js web application
├── backend/                  # Python FastAPI server
├── ai-models/               # Custom model training
├── legal-templates/         # Letter and document templates
├── docker/                  # Docker configurations
└── docs/                    # Documentation
```

## Quick Start

1. Clone the repository
2. Set up the backend: `cd backend && pip install -r requirements.txt`
3. Set up the frontend: `cd frontend && npm install`
4. Configure environment variables
5. Run development servers

## Development Setup

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

Create `.env` files in both frontend and backend directories:

### Backend (.env)
```
GEMINI_API_KEY=your_gemini_api_key
DATABASE_URL=postgresql://username:password@localhost:5432/tenant_rights
REDIS_URL=redis://localhost:6379
SECRET_KEY=your_secret_key
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000
```