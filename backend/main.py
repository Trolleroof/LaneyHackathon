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
    allow_origins=["http://localhost:3000", "http://localhost:3001", "https://your-frontend-domain.com"],
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
        import traceback
        error_details = traceback.format_exc()
        print(f"Document processing error: {error_details}")
        error_msg = str(e) if str(e) else "Unknown error occurred"
        raise HTTPException(status_code=500, detail=f"Error processing document: {error_msg}\n\nFull traceback: {error_details[:500]}")

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

@app.post("/api/chat")
async def tenant_chat(
    question: str,
    document_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Chat interface for tenant questions about lease terms and rights
    """
    try:
        context = ""
        
        # If document_id provided, get context from the lease
        if document_id:
            document = await document_service.get_document_by_id(document_id, current_user["id"], db)
            if document:
                context = document.get("extracted_text", "")
        
        answer = await ai_service.answer_tenant_question(question, context)
        
        return {
            "question": question,
            "answer": answer,
            "document_id": document_id,
            "has_context": bool(context)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@app.get("/api/letter-templates")
async def get_letter_templates():
    """
    Get available letter templates
    """
    try:
        templates = letter_service.get_letter_templates()
        return {"templates": templates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving templates: {str(e)}")

@app.get("/api/dashboard")
async def get_user_dashboard(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get user dashboard with document summaries and quick stats
    """
    try:
        documents = await document_service.get_user_documents(current_user["id"], db)
        letters = await letter_service.get_user_letters(current_user["id"], db)
        
        # Calculate summary statistics
        total_documents = len(documents)
        total_letters = len(letters)
        
        high_risk_count = 0
        medium_risk_count = 0
        recent_documents = []
        
        for doc in documents[:5]:  # Get last 5 documents
            analysis = doc.get("analysis", {})
            unfair_clauses = analysis.get("unfair_clauses", [])
            
            # Count risk levels
            for clause in unfair_clauses:
                if clause.get("severity") == "high":
                    high_risk_count += 1
                elif clause.get("severity") == "medium":
                    medium_risk_count += 1
            
            recent_documents.append({
                "id": doc["id"],
                "filename": doc["filename"],
                "overall_score": analysis.get("overall_score", 0),
                "created_at": doc["created_at"],
                "risk_level": "high" if analysis.get("overall_score", 0) < 50 else "medium" if analysis.get("overall_score", 0) < 75 else "low"
            })
        
        return {
            "user_stats": {
                "total_documents_analyzed": total_documents,
                "total_letters_generated": total_letters,
                "high_risk_clauses_found": high_risk_count,
                "medium_risk_clauses_found": medium_risk_count
            },
            "recent_documents": recent_documents,
            "quick_actions": [
                {"action": "upload_document", "label": "Analyze New Lease", "icon": "document"},
                {"action": "generate_letter", "label": "Write Letter to Landlord", "icon": "letter"},
                {"action": "ask_question", "label": "Ask About Your Rights", "icon": "chat"},
                {"action": "view_templates", "label": "Browse Letter Templates", "icon": "templates"}
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading dashboard: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    ) 