import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import google.generativeai as genai
from models.schemas import ChatMessage, ChatRequest, ChatResponse
from services.document_service import DocumentService

class ChatService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key and api_key != "your_gemini_api_key_here":
            genai.configure(api_key=api_key)
            self.gemini_client = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.gemini_client = None
            print("Warning: Gemini API key not set. Chat will return demo responses.")
        
        # In-memory storage for development
        self.chat_sessions = {}
        self.next_chat_id = 1
        
        # Document service for context
        self.document_service = DocumentService()
    
    async def chat(
        self,
        user_id: int,
        message: str,
        document_id: Optional[int] = None,
        chat_history: List[ChatMessage] = None,
        db = None
    ) -> ChatResponse:
        """
        Handle a chat message from the user
        """
        if chat_history is None:
            chat_history = []
        
        try:
            # Get document context if provided
            document_context = ""
            if document_id:
                document = await self.document_service.get_document_by_id(document_id, user_id, db)
                if document:
                    document_context = f"""
DOCUMENT CONTEXT:
Filename: {document.get('filename', 'Unknown')}
Analysis Summary: {document.get('analysis_data', {}).get('plain_english_summary', '')}
Key Issues Found: {len(document.get('analysis_data', {}).get('unfair_clauses', []))} problematic clauses
"""
            
            # Build conversation context
            conversation_context = self._build_conversation_context(chat_history, document_context)
            
            # Generate response
            if not self.gemini_client:
                return ChatResponse(
                    response="Demo response: I'm a tenant rights assistant. Please set your Gemini API key to get real legal guidance and answers to your questions.",
                    suggested_questions=[
                        "What are my rights as a tenant?",
                        "Can my landlord increase my rent?",
                        "What should I do about repairs?"
                    ],
                    references=["Demo reference - API key required"]
                )
            
            # Create the prompt for the AI
            prompt = self._create_chat_prompt(message, conversation_context, document_context)
            
            response = self.gemini_client.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=1024,
                )
            )
            
            # Parse the response
            ai_response = response.text
            
            # Extract suggested questions and references
            suggested_questions = self._extract_suggested_questions(ai_response, message)
            references = self._extract_references(ai_response)
            
            # Save chat session (in production, save to database)
            chat_id = self._save_chat_message(user_id, message, ai_response)
            
            return ChatResponse(
                response=ai_response,
                suggested_questions=suggested_questions,
                references=references,
                chat_id=chat_id
            )
            
        except Exception as e:
            raise Exception(f"Chat service error: {str(e)}")
    
    def _create_chat_prompt(self, user_message: str, conversation_context: str, document_context: str) -> str:
        """Create the prompt for the AI chat assistant"""
        return f"""You are TenantRights AI, a helpful and knowledgeable tenant rights assistant. You provide accurate legal information, practical advice, and empathetic support to tenants dealing with housing issues.

GUIDELINES:
- Provide accurate information about tenant rights and landlord-tenant law
- Be empathetic and supportive while remaining professional
- Always recommend consulting with a lawyer for complex legal issues
- Cite relevant laws when applicable (focus on general principles)
- Give practical, actionable advice
- Be concise but thorough
- If you don't know something, say so and suggest where to find authoritative information

{document_context}

CONVERSATION HISTORY:
{conversation_context}

USER QUESTION: {user_message}

Provide a helpful, accurate response. If referring to specific document analysis, make it clear. Always be supportive and practical in your advice."""

    def _build_conversation_context(self, chat_history: List[ChatMessage], document_context: str) -> str:
        """Build conversation context from chat history"""
        if not chat_history:
            return "This is the start of a new conversation."
        
        context = ""
        for msg in chat_history[-5:]:  # Keep last 5 messages for context
            role = "User" if msg.role == "user" else "Assistant"
            context += f"{role}: {msg.content}\n"
        
        return context
    
    def _extract_suggested_questions(self, ai_response: str, user_message: str) -> List[str]:
        """Extract or generate suggested follow-up questions"""
        # In a real implementation, you might parse the AI response for suggestions
        # For now, provide context-aware suggestions based on the user's question
        
        question_lower = user_message.lower()
        
        if "rent" in question_lower:
            return [
                "What notice is required for rent increases?",
                "Can I withhold rent for repairs?",
                "What are rent control laws in my area?"
            ]
        elif "repair" in question_lower or "maintenance" in question_lower:
            return [
                "How long does my landlord have to make repairs?",
                "What if my landlord won't respond to repair requests?",
                "Can I make repairs and deduct from rent?"
            ]
        elif "evict" in question_lower:
            return [
                "What are valid reasons for eviction?",
                "How much notice is required for eviction?",
                "What should I do if I receive an eviction notice?"
            ]
        elif "deposit" in question_lower:
            return [
                "When should I get my security deposit back?",
                "Can my landlord keep my deposit for normal wear and tear?",
                "What documentation should I provide?"
            ]
        else:
            return [
                "What are my basic rights as a tenant?",
                "How do I document issues with my rental?",
                "Where can I get legal help in my area?"
            ]
    
    def _extract_references(self, ai_response: str) -> List[str]:
        """Extract legal references or concepts mentioned"""
        # This is a simplified implementation
        # In production, you might use NLP to extract legal concepts
        common_references = [
            "Implied warranty of habitability",
            "Right to quiet enjoyment",
            "Fair Housing Act",
            "Local tenant protection laws",
            "Lease agreement terms",
            "Security deposit regulations"
        ]
        
        references = []
        response_lower = ai_response.lower()
        
        for ref in common_references:
            if any(word in response_lower for word in ref.lower().split()):
                references.append(ref)
        
        return references[:3]  # Limit to 3 references
    
    def _save_chat_message(self, user_id: int, user_message: str, ai_response: str) -> int:
        """Save chat message to storage (in-memory for development)"""
        chat_id = self.next_chat_id
        self.next_chat_id += 1
        
        self.chat_sessions[chat_id] = {
            "id": chat_id,
            "user_id": user_id,
            "messages": [
                {"role": "user", "content": user_message, "timestamp": datetime.now()},
                {"role": "assistant", "content": ai_response, "timestamp": datetime.now()}
            ],
            "created_at": datetime.now()
        }
        
        return chat_id
    
    async def get_chat_history(self, user_id: int, chat_id: int = None) -> List[Dict[str, Any]]:
        """Get chat history for a user"""
        if chat_id:
            session = self.chat_sessions.get(chat_id)
            if session and session["user_id"] == user_id:
                return [session]
            return []
        
        # Return all sessions for user
        return [
            session for session in self.chat_sessions.values()
            if session["user_id"] == user_id
        ]
    
    def get_common_questions(self) -> List[Dict[str, str]]:
        """Get list of common tenant questions"""
        return [
            {
                "category": "Rent & Payments",
                "questions": [
                    "Can my landlord increase my rent mid-lease?",
                    "What happens if I'm late on rent?",
                    "Are there limits on how much rent can be increased?"
                ]
            },
            {
                "category": "Repairs & Maintenance",
                "questions": [
                    "What repairs is my landlord responsible for?",
                    "How long does my landlord have to fix problems?",
                    "Can I withhold rent if repairs aren't made?"
                ]
            },
            {
                "category": "Privacy & Entry",
                "questions": [
                    "Can my landlord enter my apartment without notice?",
                    "What is considered proper notice for entry?",
                    "What can I do about unauthorized entry?"
                ]
            },
            {
                "category": "Security Deposits",
                "questions": [
                    "When should I get my security deposit back?",
                    "What can landlords deduct from deposits?",
                    "How do I dispute deposit deductions?"
                ]
            },
            {
                "category": "Evictions",
                "questions": [
                    "What are valid reasons for eviction?",
                    "How much notice is required for eviction?",
                    "What are my rights during eviction proceedings?"
                ]
            }
        ] 