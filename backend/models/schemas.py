from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class SeverityLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"  
    LOW = "low"

class ImportanceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class LetterType(str, Enum):
    REPAIR_REQUEST = "repair_request"
    RENT_DISPUTE = "rent_dispute"
    SECURITY_DEPOSIT = "security_deposit"
    NO_NOTICE_ENTRY = "no_notice_entry"
    NOISE_COMPLAINT = "noise_complaint"
    LEASE_VIOLATION = "lease_violation"
    DISCRIMINATION = "discrimination"
    HABITABILITY = "habitability"
    GENERAL_CONCERN = "general_concern"

# Core Analysis Models
class ClauseAnalysis(BaseModel):
    clause_text: str = Field(..., description="The exact text of the problematic clause")
    issue: str = Field(..., description="Brief description of why this clause is problematic")
    severity: SeverityLevel = Field(..., description="How severe this issue is")
    explanation: str = Field(..., description="Plain English explanation of the problem")
    recommendation: str = Field(..., description="What the tenant should do about this clause")

class TenantRight(BaseModel):
    title: str = Field(..., description="Name of the tenant right")
    description: str = Field(..., description="What this right means for the tenant")
    importance: ImportanceLevel = Field(..., description="How important this right is")

class DocumentAnalysis(BaseModel):
    unfair_clauses: List[ClauseAnalysis] = Field(default=[], description="List of problematic clauses found")
    plain_english_summary: str = Field(..., description="Simple summary of the entire lease")
    tenant_rights: List[TenantRight] = Field(default=[], description="Key tenant rights and obligations")
    recommendations: List[str] = Field(default=[], description="Actionable recommendations for the tenant")
    overall_score: float = Field(..., description="Overall fairness score (0-100, higher is better)")

# API Request/Response Models
class DocumentAnalysisResponse(BaseModel):
    document_id: int = Field(..., description="Unique identifier for the analyzed document")
    filename: str = Field(..., description="Original filename of the uploaded document")
    extracted_text: str = Field(..., description="Text extracted from the document via OCR")
    analysis: DocumentAnalysis = Field(..., description="AI analysis results")
    unfair_clauses: List[ClauseAnalysis] = Field(..., description="Problematic clauses (convenience field)")
    plain_english_summary: str = Field(..., description="Simple summary (convenience field)")
    tenant_rights: List[TenantRight] = Field(..., description="Tenant rights (convenience field)")
    recommendations: List[str] = Field(..., description="Recommendations (convenience field)")
    created_at: Optional[datetime] = None
    
class TenantInfo(BaseModel):
    name: str = Field(..., description="Tenant's full name")
    address: str = Field(..., description="Rental property address")
    phone: Optional[str] = None
    email: Optional[str] = None
    lease_start_date: Optional[str] = None
    monthly_rent: Optional[float] = None

class LandlordInfo(BaseModel):
    name: str = Field(..., description="Landlord or property manager name")
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    company_name: Optional[str] = None

class LetterGenerationRequest(BaseModel):
    letter_type: LetterType = Field(..., description="Type of letter to generate")
    context: str = Field(..., description="Specific context or situation details")
    tenant_info: TenantInfo = Field(..., description="Tenant's information")
    landlord_info: LandlordInfo = Field(..., description="Landlord's information")
    specific_issues: List[str] = Field(default=[], description="Specific issues to address")
    requested_action: Optional[str] = None
    deadline: Optional[str] = None

class LetterGenerationResponse(BaseModel):
    letter_id: int = Field(..., description="Unique identifier for the generated letter")
    letter_type: LetterType = Field(..., description="Type of letter generated")
    content: str = Field(..., description="Generated letter content")
    created_at: Optional[datetime] = None

# Database Models (for reference)
class UserDocument(BaseModel):
    id: int
    user_id: int
    filename: str
    file_path: str
    extracted_text: str
    analysis_data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class GeneratedLetter(BaseModel):
    id: int
    user_id: int
    letter_type: LetterType
    content: str
    context: Dict[str, Any]
    created_at: datetime

# Utility Models
class ClauseExplanationRequest(BaseModel):
    clause_text: str = Field(..., description="The lease clause to explain")

class ClauseExplanationResponse(BaseModel):
    clause: str = Field(..., description="The original clause text")
    explanation: str = Field(..., description="Plain English explanation")
    is_problematic: Optional[bool] = None
    severity: Optional[SeverityLevel] = None
    recommendation: Optional[str] = None

class SimilarClause(BaseModel):
    clause: str = Field(..., description="Similar clause text")
    issue: str = Field(..., description="The problem with this clause")
    explanation: str = Field(..., description="Why it's problematic")
    severity: SeverityLevel = Field(..., description="Severity level")

class DocumentListResponse(BaseModel):
    documents: List[UserDocument] = Field(..., description="List of user's documents")

class LetterListResponse(BaseModel):
    letters: List[GeneratedLetter] = Field(..., description="List of user's generated letters")

# Error Models
class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    detail: Optional[str] = None
    error_code: Optional[str] = None

# Status Models
class HealthResponse(BaseModel):
    status: str = Field(..., description="Service health status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.now)

class UploadStatus(BaseModel):
    status: str = Field(..., description="Upload processing status")
    message: str = Field(..., description="Status message")
    progress: Optional[float] = None 