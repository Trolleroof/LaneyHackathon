from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import uvicorn
from dotenv import load_dotenv
import os
from typing import Optional, List
import asyncio

from services.ocr_service import OCRService
from services.ai_service import AIService
from services.document_service import DocumentService
from services.letter_service import LetterService
from models.schemas import (
    DocumentAnalysisResponse,
    ClauseAnalysis,
    LetterGenerationRequest,
    LetterGenerationResponse
)
from database import get_db
from auth import get_current_user

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="TenantRights AI Assistant API",
    description="AI-powered assistant for analyzing lease agreements and generating tenant correspondence",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Initialize services
ocr_service = OCRService()
ai_service = AIService()
document_service = DocumentService()
letter_service = LetterService()

@app.get("/")
async def root():
    return {"message": "TenantRights AI Assistant API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

@app.post("/api/upload-document", response_model=DocumentAnalysisResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Upload and analyze a lease document
    """
    try:
        # Validate file type
        allowed_types = ['application/pdf', 'image/jpeg', 'image/png', 'image/tiff']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail="Invalid file type. Please upload PDF or image files."
            )
        
        # Read file content
        file_content = await file.read()
        
        # Extract text using OCR
        extracted_text = await ocr_service.extract_text(file_content, file.content_type)
        
        # Analyze document with AI
        analysis = await ai_service.analyze_lease_document(extracted_text)
        
        # Save document analysis to database
        document_id = await document_service.save_document_analysis(
            user_id=current_user["id"],
            filename=file.filename,
            extracted_text=extracted_text,
            analysis=analysis,
            db=db
        )
        
        return DocumentAnalysisResponse(
            document_id=document_id,
            filename=file.filename,
            extracted_text=extracted_text,
            analysis=analysis,
            unfair_clauses=analysis.unfair_clauses,
            plain_english_summary=analysis.plain_english_summary,
            tenant_rights=analysis.tenant_rights,
            recommendations=analysis.recommendations
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@app.post("/api/generate-letter", response_model=LetterGenerationResponse)
async def generate_letter(
    request: LetterGenerationRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Generate a formal letter or dispute document
    """
    try:
        # Generate letter using AI
        generated_letter = await letter_service.generate_letter(
            letter_type=request.letter_type,
            context=request.context,
            tenant_info=request.tenant_info,
            landlord_info=request.landlord_info,
            specific_issues=request.specific_issues
        )
        
        # Save generated letter to database
        letter_id = await letter_service.save_letter(
            user_id=current_user["id"],
            letter_type=request.letter_type,
            content=generated_letter,
            db=db
        )
        
        return LetterGenerationResponse(
            letter_id=letter_id,
            letter_type=request.letter_type,
            content=generated_letter,
            created_at=None  # Will be populated by the service
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating letter: {str(e)}")

@app.get("/api/documents/{document_id}")
async def get_document_analysis(
    document_id: int,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Retrieve a previously analyzed document
    """
    document = await document_service.get_document_by_id(document_id, current_user["id"], db)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@app.get("/api/user/documents")
async def get_user_documents(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get all documents for the current user
    """
    documents = await document_service.get_user_documents(current_user["id"], db)
    return {"documents": documents}

@app.get("/api/user/letters")
async def get_user_letters(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get all generated letters for the current user
    """
    letters = await letter_service.get_user_letters(current_user["id"], db)
    return {"letters": letters}

@app.post("/api/explain-clause")
async def explain_clause(
    clause_text: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a plain English explanation of a specific lease clause
    """
    try:
        explanation = await ai_service.explain_clause(clause_text)
        return {"clause": clause_text, "explanation": explanation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error explaining clause: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    ) 