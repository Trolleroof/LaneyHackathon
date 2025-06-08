import os
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from langchain.text_splitter import RecursiveCharacterTextSplitter
import chromadb
from sentence_transformers import SentenceTransformer
import json
from dotenv import load_dotenv

from models.schemas import DocumentAnalysis, ClauseAnalysis, TenantRight

load_dotenv()

class AIService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "your_gemini_api_key_here":
            print("Warning: Gemini API key not set. AI features will be limited.")
            self.gemini_client = None
        else:
            genai.configure(api_key=api_key)
            self.gemini_client = genai.GenerativeModel('gemini-1.5-flash')
        
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.chroma_client = chromadb.Client()
        
        # Initialize legal knowledge base collection
        try:
            self.legal_collection = self.chroma_client.get_collection("legal_clauses")
        except:
            self.legal_collection = self.chroma_client.create_collection("legal_clauses")
            self._populate_legal_knowledge_base()
    
    def _populate_legal_knowledge_base(self):
        """Initialize the legal knowledge base with common problematic clauses"""
        problematic_clauses = [
            {
                "clause": "Landlord may enter premises at any time without notice",
                "issue": "Violates tenant privacy rights",
                "explanation": "Most states require 24-48 hours notice except for emergencies",
                "severity": "high"
            },
            {
                "clause": "Tenant responsible for all repairs regardless of cause",
                "issue": "Unfair maintenance responsibility",
                "explanation": "Landlord is typically responsible for structural and major repairs",
                "severity": "high"
            },
            {
                "clause": "No pets allowed under any circumstances",
                "issue": "May violate disability accommodation laws",
                "explanation": "Service animals and emotional support animals may be required by law",
                "severity": "medium"
            },
            {
                "clause": "Security deposit is non-refundable",
                "issue": "Violates security deposit laws",
                "explanation": "Security deposits must be refundable minus legitimate damages",
                "severity": "high"
            },
            {
                "clause": "Rent can be increased at any time with 3 days notice",
                "issue": "Insufficient notice period",
                "explanation": "Most states require 30 days notice for rent increases",
                "severity": "medium"
            }
        ]
        
        for i, clause_data in enumerate(problematic_clauses):
            embedding = self.embedding_model.encode(clause_data["clause"]).tolist()
            self.legal_collection.add(
                embeddings=[embedding],
                documents=[clause_data["clause"]],
                metadatas=[{
                    "issue": clause_data["issue"],
                    "explanation": clause_data["explanation"],
                    "severity": clause_data["severity"]
                }],
                ids=[f"clause_{i}"]
            )
    
    async def analyze_lease_document(self, document_text: str, language: str = "en") -> DocumentAnalysis:
        """
        Analyze a lease document for unfair clauses and provide explanations
        """
        try:
            # Split document into chunks for better processing
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=2000,
                chunk_overlap=200
            )
            chunks = text_splitter.split_text(document_text)
            
            # Analyze each chunk
            all_unfair_clauses = []
            all_tenant_rights = []
            
            for chunk in chunks:
                # Find potentially problematic clauses
                unfair_clauses = await self._identify_unfair_clauses(chunk, language)
                all_unfair_clauses.extend(unfair_clauses)
                
                # Extract tenant rights information
                tenant_rights = await self._extract_tenant_rights(chunk, language)
                all_tenant_rights.extend(tenant_rights)
            
            # Generate overall summary
            plain_english_summary = await self._generate_plain_english_summary(document_text, language)
            
            # Limit to top 20 most severe problematic clauses
            # Sort by severity (high > medium > low) and limit to 20
            severity_order = {'high': 3, 'medium': 2, 'low': 1}
            all_unfair_clauses.sort(key=lambda x: severity_order.get(x.severity, 0), reverse=True)
            limited_unfair_clauses = all_unfair_clauses[:20]
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(limited_unfair_clauses, language)
            
            return DocumentAnalysis(
                unfair_clauses=limited_unfair_clauses,
                plain_english_summary=plain_english_summary,
                tenant_rights=all_tenant_rights,
                recommendations=recommendations,
                overall_score=self._calculate_overall_score(limited_unfair_clauses)
            )
            
        except Exception as e:
            raise Exception(f"Error analyzing document: {str(e)}")
    
    async def _identify_unfair_clauses(self, text_chunk: str, language: str = "en") -> List[ClauseAnalysis]:
        """
        Identify potentially unfair or problematic clauses in a text chunk
        """
        # Force English if language parameter is 'en' or not specified properly
        if language not in ["es", "fr", "de", "it", "pt", "zh", "ja", "ko", "ar"]:
            language = "en"
        
        # Enhanced language mapping with stronger instructions
        language_instructions = {
            "en": "RESPOND ONLY IN ENGLISH. DO NOT USE SPANISH OR ANY OTHER LANGUAGE. ALL TEXT MUST BE IN ENGLISH.",
            "es": "Responde ÚNICAMENTE en español. NO uses inglés ni ningún otro idioma.",
            "fr": "Répondez UNIQUEMENT en français. N'utilisez pas l'anglais ou d'autres langues.", 
            "de": "Antworten Sie NUR auf Deutsch. Verwenden Sie kein Englisch oder andere Sprachen.",
            "it": "Rispondi SOLO in italiano. Non usare inglese o altre lingue.",
            "pt": "Responda APENAS em português. Não use inglês ou outras línguas.",
            "zh": "只用中文回答。不要使用英文或其他语言。",
            "ja": "日本語のみで回答してください。英語や他の言語を使用しないでください。",
            "ko": "한국어로만 답변해주세요. 영어나 다른 언어를 사용하지 마세요.",
            "ar": "أجب باللغة العربية فقط. لا تستخدم الإنجليزية أو أي لغة أخرى."
        }
        
        lang_instruction = language_instructions.get(language, language_instructions["en"])
        
        prompt = f"""
        You are a tenant rights expert lawyer. Analyze the following lease text and identify potentially unfair, illegal, or problematic clauses.
        
        CRITICAL LANGUAGE INSTRUCTION: {lang_instruction}
        
        IMPORTANT: You MUST write ALL text fields (clause_text, issue, explanation, recommendation) in the specified language. 
        If the language is 'en' or English, write EVERYTHING in English. 
        If the language is 'es' or Spanish, write EVERYTHING in Spanish.
        DO NOT MIX LANGUAGES. STAY CONSISTENT WITH THE SPECIFIED LANGUAGE.

        Lease text:
        {{text}}

        For each problematic clause you find, provide:
        1. A summary of the clause (in the specified language)
        2. Why it's problematic (in the specified language)
        3. The severity (high, medium, low)
        4. Clear explanation in the specified language
        5. Recommended action in the specified language

        Format your response as JSON with this structure:
        {{{{
            "clauses": [
                {{{{
                    "clause_text": "summary of the clause in the specified language",
                    "issue": "brief description of the problem in the specified language",
                    "severity": "high/medium/low",
                    "explanation": "clear explanation in the specified language",
                    "recommendation": "what the tenant should do in the specified language"
                }}}}
            ]
        }}}}
        """
        
        try:
            if not self.gemini_client:
                # Return mock data when API key is not available
                return [ClauseAnalysis(
                    clause_text="Demo clause analysis",
                    issue="Gemini API key required for full analysis",
                    severity="low",
                    explanation="Please set your Gemini API key to get detailed clause analysis",
                    recommendation="Add your Gemini API key to the .env file"
                )]
            
            response = self.gemini_client.generate_content(
                f"You are a helpful tenant rights lawyer. Follow the language instructions exactly. ONLY respond with valid JSON, no extra text.\n\n{prompt.format(text=text_chunk)}",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Lower temperature for more consistent output
                    max_output_tokens=2048,
                )
            )
            
            # Clean up the response text and extract JSON
            response_text = response.text.strip()
            
            # Try to find JSON in the response
            try:
                # First try parsing as-is
                result = json.loads(response_text)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                import re
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                else:
                    # If no JSON found, create a basic response
                    print(f"Could not parse JSON from response: {response_text[:200]}...")
                    return [ClauseAnalysis(
                        clause_text="Analysis unavailable",
                        issue="JSON parsing error",
                        severity="low",
                        explanation="The AI response could not be parsed properly",
                        recommendation="Try uploading the document again"
                    )]
            
            clause_analyses = []
            for clause_data in result.get("clauses", []):
                clause_analyses.append(ClauseAnalysis(
                    clause_text=clause_data["clause_text"],
                    issue=clause_data["issue"],
                    severity=clause_data["severity"],
                    explanation=clause_data["explanation"],
                    recommendation=clause_data["recommendation"]
                ))
            
            return clause_analyses
            
        except Exception as e:
            print(f"Error identifying unfair clauses: {str(e)}")
            return []
    
    async def _extract_tenant_rights(self, text_chunk: str, language: str = "en") -> List[TenantRight]:
        """
        Extract tenant rights and obligations from the lease text
        """
        # Force English if language parameter is 'en' or not specified properly
        if language not in ["es", "fr", "de", "it", "pt", "zh", "ja", "ko", "ar"]:
            language = "en"
        
        # Enhanced language mapping with stronger instructions
        language_instructions = {
            "en": "RESPOND ONLY IN ENGLISH. DO NOT USE SPANISH OR ANY OTHER LANGUAGE. ALL TEXT MUST BE IN ENGLISH.",
            "es": "Responde ÚNICAMENTE en español. NO uses inglés ni ningún otro idioma.",
            "fr": "Répondez UNIQUEMENT en français. N'utilisez pas l'anglais ou d'autres langues.", 
            "de": "Antworten Sie NUR auf Deutsch. Verwenden Sie kein Englisch oder andere Sprachen.",
            "it": "Rispondi SOLO in italiano. Non usare inglese o altre lingue.",
            "pt": "Responda APENAS em português. Não use inglês ou outras línguas.",
            "zh": "只用中文回答。不要使用英文或其他语言。",
            "ja": "日本語のみで回答してください。英語や他の言語を使用しないでください。",
            "ko": "한국어로만 답변해주세요. 영어나 다른 언어를 사용하지 마세요.",
            "ar": "أجب باللغة العربية فقط. لا تستخدم الإنجليزية أو أي لغة أخرى."
        }
        
        lang_instruction = language_instructions.get(language, language_instructions["en"])
        
        prompt = f"""
        Analyze this lease text and extract the key tenant rights and obligations.
        
        CRITICAL LANGUAGE INSTRUCTION: {lang_instruction}
        
        IMPORTANT: You MUST write ALL text fields (title, description) in the specified language. 
        If the language is 'en' or English, write EVERYTHING in English. 
        If the language is 'es' or Spanish, write EVERYTHING in Spanish.
        DO NOT MIX LANGUAGES. STAY CONSISTENT WITH THE SPECIFIED LANGUAGE.

        Lease text:
        {{text}}

        Identify:
        1. Rights the tenant has (in the specified language)
        2. Obligations the tenant must fulfill (in the specified language)
        3. Important deadlines or procedures (in the specified language)

        Format as JSON:
        {{{{
            "rights": [
                {{{{
                    "title": "Right name in the specified language",
                    "description": "What this right means in the specified language",
                    "importance": "high/medium/low"
                }}}}
            ]
        }}}}
        """
        
        try:
            if not self.gemini_client:
                # Return mock data when API key is not available
                return [TenantRight(
                    title="Demo tenant right",
                    description="Gemini API key required for detailed rights analysis",
                    importance="low"
                )]
            
            response = self.gemini_client.generate_content(
                f"You are a tenant rights expert. Follow the language instructions exactly. ONLY respond with valid JSON, no extra text.\n\n{prompt.format(text=text_chunk)}",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Lower temperature for more consistent output
                    max_output_tokens=2048,
                )
            )
            
            # Clean up the response text and extract JSON
            response_text = response.text.strip()
            
            # Try to find JSON in the response
            try:
                # First try parsing as-is
                result = json.loads(response_text)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                import re
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                else:
                    # If no JSON found, create a basic response
                    print(f"Could not parse tenant rights JSON from response: {response_text[:200]}...")
                    return [TenantRight(
                        title="Analysis unavailable",
                        description="The AI response could not be parsed properly",
                        importance="low"
                    )]
            
            tenant_rights = []
            for right_data in result.get("rights", []):
                tenant_rights.append(TenantRight(
                    title=right_data["title"],
                    description=right_data["description"],
                    importance=right_data["importance"]
                ))
            
            return tenant_rights
            
        except Exception as e:
            print(f"Error extracting tenant rights: {str(e)}")
            return []
    
    async def _generate_plain_english_summary(self, document_text: str, language: str = "en") -> str:
        """
        Generate a plain English summary of the lease document
        """
        # Force English if language parameter is 'en' or not specified properly
        if language not in ["es", "fr", "de", "it", "pt", "zh", "ja", "ko", "ar"]:
            language = "en"
        
        # Enhanced language mapping with stronger instructions
        language_instructions = {
            "en": "RESPOND ONLY IN ENGLISH. DO NOT USE SPANISH OR ANY OTHER LANGUAGE. ALL TEXT MUST BE IN ENGLISH.",
            "es": "Responde ÚNICAMENTE en español. NO uses inglés ni ningún otro idioma.",
            "fr": "Répondez UNIQUEMENT en français. N'utilisez pas l'anglais ou d'autres langues.", 
            "de": "Antworten Sie NUR auf Deutsch. Verwenden Sie kein Englisch oder andere Sprachen.",
            "it": "Rispondi SOLO in italiano. Non usare inglese o altre lingue.",
            "pt": "Responda APENAS em português. Não use inglês ou outras línguas.",
            "zh": "只用中文回答。不要使用英文或其他语言。",
            "ja": "日本語のみで回答してください。英語や他の言語を使用しないでください。",
            "ko": "한국어로만 답변해주세요. 영어나 다른 언어를 사용하지 마세요.",
            "ar": "أجب باللغة العربية فقط. لا تستخدم الإنجليزية أو أي لغة أخرى."
        }
        
        lang_instruction = language_instructions.get(language, language_instructions["en"])
        
        prompt = f"""
        You are helping low-income renters understand their lease agreements. 
        Summarize this lease document in plain, simple language that a 6th grader could understand.
        
        CRITICAL LANGUAGE INSTRUCTION: {lang_instruction}
        
        IMPORTANT: You MUST write the ENTIRE summary in the specified language. 
        If the language is 'en' or English, write EVERYTHING in English. 
        If the language is 'es' or Spanish, write EVERYTHING in Spanish.
        DO NOT MIX LANGUAGES. STAY CONSISTENT WITH THE SPECIFIED LANGUAGE.

        Focus on:
        - Key terms and conditions
        - Important dates and deadlines  
        - What the tenant needs to know
        - Any red flags or concerns

        Keep it under 300 words and use simple language in the specified language.

        Lease document:
        {{text}}
        """
        
        try:
            if not self.gemini_client:
                return "Demo summary: This is a sample lease analysis. Please set your Gemini API key to get detailed document analysis and plain English summaries of your lease agreement."
            
            response = self.gemini_client.generate_content(
                f"You are a helpful legal assistant who explains things simply. Follow the language instructions exactly.\n\n{prompt.format(text=document_text[:4000])}",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=2048,
                )
            )
            
            return response.text
            
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    async def _generate_recommendations(self, unfair_clauses: List[ClauseAnalysis], language: str = "en") -> List[str]:
        """
        Generate actionable recommendations based on identified issues
        """
        # Language-specific recommendations
        recommendations_by_language = {
            "en": {
                "standard": "Your lease appears to be fairly standard. Review it carefully and keep a copy for your records.",
                "urgent": "🚨 URGENT: This lease contains potentially illegal clauses. Consider consulting with a tenant rights organization or legal aid before signing.",
                "multiple": "⚠️ Multiple concerning clauses found. Document everything and consider negotiating with your landlord.",
                "general": [
                    "📋 Keep detailed records of all communications with your landlord",
                    "📞 Know your local tenant rights hotline number",
                    "💰 Understand your security deposit rights",
                    "🏠 Take photos of the property condition before moving in"
                ]
            },
            "es": {
                "standard": "Su contrato de arrendamiento parece ser bastante estándar. Revíselo cuidadosamente y guarde una copia para sus registros.",
                "urgent": "🚨 URGENTE: Este contrato contiene cláusulas potencialmente ilegales. Considere consultar con una organización de derechos de inquilinos o asistencia legal antes de firmar.",
                "multiple": "⚠️ Se encontraron múltiples cláusulas preocupantes. Documente todo y considere negociar con su arrendador.",
                "general": [
                    "📋 Mantenga registros detallados de todas las comunicaciones con su arrendador",
                    "📞 Conozca el número de la línea directa de derechos de inquilinos de su localidad",
                    "💰 Comprenda sus derechos sobre el depósito de seguridad",
                    "🏠 Tome fotos del estado de la propiedad antes de mudarse"
                ]
            },
            "fr": {
                "standard": "Votre bail semble être assez standard. Examinez-le attentivement et gardez une copie pour vos dossiers.",
                "urgent": "🚨 URGENT: Ce bail contient des clauses potentiellement illégales. Envisagez de consulter une organisation de droits des locataires ou une aide juridique avant de signer.",
                "multiple": "⚠️ Plusieurs clauses préoccupantes trouvées. Documentez tout et envisagez de négocier avec votre propriétaire.",
                "general": [
                    "📋 Tenez des registres détaillés de toutes les communications avec votre propriétaire",
                    "📞 Connaissez le numéro de la ligne d'assistance des droits des locataires de votre région",
                    "💰 Comprenez vos droits concernant le dépôt de garantie",
                    "🏠 Prenez des photos de l'état de la propriété avant d'emménager"
                ]
            },
            "de": {
                "standard": "Ihr Mietvertrag scheint ziemlich standard zu sein. Prüfen Sie ihn sorgfältig und bewahren Sie eine Kopie für Ihre Unterlagen auf.",
                "urgent": "🚨 DRINGEND: Dieser Mietvertrag enthält möglicherweise illegale Klauseln. Erwägen Sie, sich vor der Unterzeichnung an eine Mieterrechtsorganisation oder Rechtshilfe zu wenden.",
                "multiple": "⚠️ Mehrere bedenkliche Klauseln gefunden. Dokumentieren Sie alles und erwägen Sie Verhandlungen mit Ihrem Vermieter.",
                "general": [
                    "📋 Führen Sie detaillierte Aufzeichnungen über alle Kommunikationen mit Ihrem Vermieter",
                    "📞 Kennen Sie die örtliche Mieterrechts-Hotline-Nummer",
                    "💰 Verstehen Sie Ihre Rechte bezüglich der Kaution",
                    "🏠 Machen Sie Fotos vom Zustand der Immobilie vor dem Einzug"
                ]
            }
        }
        
        # Default to English if language not supported
        recs = recommendations_by_language.get(language, recommendations_by_language["en"])
        
        if not unfair_clauses:
            return [recs["standard"]]
        
        high_severity = [c for c in unfair_clauses if c.severity == "high"]
        medium_severity = [c for c in unfair_clauses if c.severity == "medium"]
        
        recommendations = []
        
        if high_severity:
            recommendations.append(recs["urgent"])
        
        if len(unfair_clauses) >= 3:
            recommendations.append(recs["multiple"])
        
        recommendations.extend(recs["general"])
        
        return recommendations
    
    def _calculate_overall_score(self, unfair_clauses: List[ClauseAnalysis]) -> float:
        """
        Calculate an overall lease fairness score (0-100, higher is better)
        """
        if not unfair_clauses:
            return 85.0  # Good but not perfect
        
        severity_weights = {"high": 20, "medium": 10, "low": 5}
        total_deduction = sum(severity_weights.get(clause.severity, 0) for clause in unfair_clauses)
        
        score = max(0, 100 - total_deduction)
        return float(score)
    
    async def explain_clause(self, clause_text: str) -> str:
        """
        Provide a plain English explanation of a specific lease clause
        """
        prompt = """
        Explain this lease clause in simple, plain English that anyone can understand:

        Clause: "{clause}"

        Provide:
        1. What it means in everyday language
        2. Why it matters to tenants
        3. Whether it's fair or potentially problematic
        4. What tenants should know about it

        Keep your explanation clear and under 200 words.
        """
        
        try:
            if not self.gemini_client:
                return "Demo explanation: This is a sample clause explanation. Please set your Gemini API key to get detailed explanations of specific lease clauses in plain English."
            
            response = self.gemini_client.generate_content(
                f"You are a helpful legal expert who explains complex terms simply.\n\n{prompt.format(clause=clause_text)}",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.4,
                    max_output_tokens=1024,
                )
            )
            
            return response.text
            
        except Exception as e:
            return f"Error explaining clause: {str(e)}"
    
    async def find_similar_clauses(self, clause_text: str, limit: int = 3) -> List[Dict]:
        """
        Find similar problematic clauses in the knowledge base
        """
        try:
            query_embedding = self.embedding_model.encode(clause_text).tolist()
            
            results = self.legal_collection.query(
                query_embeddings=[query_embedding],
                n_results=limit
            )
            
            similar_clauses = []
            for i, doc in enumerate(results['documents'][0]):
                similar_clauses.append({
                    "clause": doc,
                    "issue": results['metadatas'][0][i]["issue"],
                    "explanation": results['metadatas'][0][i]["explanation"],
                    "severity": results['metadatas'][0][i]["severity"]
                })
            
            return similar_clauses
            
        except Exception as e:
            print(f"Error finding similar clauses: {str(e)}")
            return []
    
    async def answer_tenant_question(self, question: str, context: str = "") -> str:
        """
        Answer tenant questions about lease terms and tenant rights
        """
        prompt = """
        You are a helpful tenant rights expert assistant. Answer this tenant's question in simple, clear language.

        {context_info}

        Question: {question}

        Provide:
        1. A direct answer to their question
        2. Relevant tenant rights information
        3. Practical advice if applicable
        4. When to seek legal help if serious

        Keep your answer under 300 words and use simple language.
        """
        
        context_info = ""
        if context:
            context_info = f"Here is text from their lease for context:\n\n{context[:2000]}\n\n"
        else:
            context_info = "No specific lease context provided.\n\n"
        
        try:
            if not self.gemini_client:
                return "Demo answer: This is a sample Q&A response. Please set your Gemini API key to get detailed answers to your tenant rights questions."
            
            response = self.gemini_client.generate_content(
                f"You are a helpful tenant rights expert who explains things simply and helps renters understand their rights.\n\n{prompt.format(context_info=context_info, question=question)}",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.4,
                    max_output_tokens=1024,
                )
            )
            
            return response.text
            
        except Exception as e:
            return f"Error answering question: {str(e)}" 