from typing import Dict, Any, List, Optional
from datetime import datetime
import json

class DocumentService:
    """
    Service for handling document storage and retrieval
    Note: This is a simple in-memory implementation for development
    In production, this would use a real database
    """
    
    def __init__(self):
        # In-memory storage for development
        self.documents = {}
        self.next_id = 1
    
    async def save_document_analysis(
        self,
        user_id: int,
        filename: str,
        extracted_text: str,
        analysis: Any,
        db = None
    ) -> int:
        """
        Save document analysis results
        """
        try:
            document_id = self.next_id
            self.next_id += 1
            
            document_data = {
                "id": document_id,
                "user_id": user_id,
                "filename": filename,
                "extracted_text": extracted_text,
                "analysis": {
                    "unfair_clauses": [
                        {
                            "clause_text": clause.clause_text,
                            "issue": clause.issue,
                            "severity": clause.severity,
                            "explanation": clause.explanation,
                            "recommendation": clause.recommendation
                        } for clause in analysis.unfair_clauses
                    ],
                    "plain_english_summary": analysis.plain_english_summary,
                    "tenant_rights": [
                        {
                            "title": right.title,
                            "description": right.description,
                            "importance": right.importance
                        } for right in analysis.tenant_rights
                    ],
                    "recommendations": analysis.recommendations,
                    "overall_score": analysis.overall_score
                },
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            self.documents[document_id] = document_data
            
            print(f"Saved document analysis with ID: {document_id}")
            return document_id
            
        except Exception as e:
            raise Exception(f"Failed to save document analysis: {str(e)}")
    
    async def get_document_by_id(
        self,
        document_id: int,
        user_id: int,
        db = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document by ID for a specific user
        """
        try:
            document = self.documents.get(document_id)
            
            if not document:
                return None
            
            # Check if user owns this document
            if document["user_id"] != user_id:
                return None
            
            return document
            
        except Exception as e:
            print(f"Error retrieving document {document_id}: {str(e)}")
            return None
    
    async def get_user_documents(
        self,
        user_id: int,
        db = None
    ) -> List[Dict[str, Any]]:
        """
        Get all documents for a user
        """
        try:
            user_documents = [
                doc for doc in self.documents.values()
                if doc["user_id"] == user_id
            ]
            
            # Sort by creation date (newest first)
            user_documents.sort(
                key=lambda x: x["created_at"],
                reverse=True
            )
            
            return user_documents
            
        except Exception as e:
            print(f"Error retrieving documents for user {user_id}: {str(e)}")
            return []
    
    async def delete_document(
        self,
        document_id: int,
        user_id: int,
        db = None
    ) -> bool:
        """
        Delete a document (with user ownership check)
        """
        try:
            document = self.documents.get(document_id)
            
            if not document:
                return False
            
            # Check if user owns this document
            if document["user_id"] != user_id:
                return False
            
            del self.documents[document_id]
            print(f"Deleted document {document_id}")
            return True
            
        except Exception as e:
            print(f"Error deleting document {document_id}: {str(e)}")
            return False
    
    async def update_document_analysis(
        self,
        document_id: int,
        user_id: int,
        updated_analysis: Any,
        db = None
    ) -> bool:
        """
        Update an existing document's analysis
        """
        try:
            document = self.documents.get(document_id)
            
            if not document:
                return False
            
            # Check if user owns this document
            if document["user_id"] != user_id:
                return False
            
            # Update analysis data
            document["analysis"] = {
                "unfair_clauses": [
                    {
                        "clause_text": clause.clause_text,
                        "issue": clause.issue,
                        "severity": clause.severity,
                        "explanation": clause.explanation,
                        "recommendation": clause.recommendation
                    } for clause in updated_analysis.unfair_clauses
                ],
                "plain_english_summary": updated_analysis.plain_english_summary,
                "tenant_rights": [
                    {
                        "title": right.title,
                        "description": right.description,
                        "importance": right.importance
                    } for right in updated_analysis.tenant_rights
                ],
                "recommendations": updated_analysis.recommendations,
                "overall_score": updated_analysis.overall_score
            }
            
            document["updated_at"] = datetime.now().isoformat()
            
            self.documents[document_id] = document
            
            print(f"Updated document analysis for ID: {document_id}")
            return True
            
        except Exception as e:
            print(f"Error updating document {document_id}: {str(e)}")
            return False
    
    def get_document_statistics(self, user_id: int) -> Dict[str, Any]:
        """
        Get statistics about user's documents
        """
        try:
            user_docs = [
                doc for doc in self.documents.values()
                if doc["user_id"] == user_id
            ]
            
            if not user_docs:
                return {
                    "total_documents": 0,
                    "average_score": 0,
                    "high_risk_documents": 0,
                    "recent_documents": 0
                }
            
            total_score = sum(doc["analysis"]["overall_score"] for doc in user_docs)
            average_score = total_score / len(user_docs)
            
            high_risk_count = sum(
                1 for doc in user_docs
                if doc["analysis"]["overall_score"] < 60
            )
            
            # Count documents from last 30 days
            thirty_days_ago = datetime.now().timestamp() - (30 * 24 * 60 * 60)
            recent_count = sum(
                1 for doc in user_docs
                if datetime.fromisoformat(doc["created_at"]).timestamp() > thirty_days_ago
            )
            
            return {
                "total_documents": len(user_docs),
                "average_score": round(average_score, 1),
                "high_risk_documents": high_risk_count,
                "recent_documents": recent_count
            }
            
        except Exception as e:
            print(f"Error calculating statistics for user {user_id}: {str(e)}")
            return {
                "total_documents": 0,
                "average_score": 0,
                "high_risk_documents": 0,
                "recent_documents": 0
            } 