import os
from typing import List, Dict, Any, Optional
import openai
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.text_splitter import RecursiveCharacterTextSplitter
import chromadb
from sentence_transformers import SentenceTransformer
import json
from dotenv import load_dotenv

from models.schemas import DocumentAnalysis, ClauseAnalysis, TenantRight

load_dotenv()

class AIService:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
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
    
    async def analyze_lease_document(self, document_text: str) -> DocumentAnalysis:
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
                unfair_clauses = await self._identify_unfair_clauses(chunk)
                all_unfair_clauses.extend(unfair_clauses)
                
                # Extract tenant rights information
                tenant_rights = await self._extract_tenant_rights(chunk)
                all_tenant_rights.extend(tenant_rights)
            
            # Generate overall summary
            plain_english_summary = await self._generate_plain_english_summary(document_text)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(all_unfair_clauses)
            
            return DocumentAnalysis(
                unfair_clauses=all_unfair_clauses,
                plain_english_summary=plain_english_summary,
                tenant_rights=all_tenant_rights,
                recommendations=recommendations,
                overall_score=self._calculate_overall_score(all_unfair_clauses)
            )
            
        except Exception as e:
            raise Exception(f"Error analyzing document: {str(e)}")
    
    async def _identify_unfair_clauses(self, text_chunk: str) -> List[ClauseAnalysis]:
        """
        Identify potentially unfair or problematic clauses in a text chunk
        """
        prompt = """
        You are a tenant rights expert lawyer. Analyze the following lease text and identify potentially unfair, illegal, or problematic clauses.

        Lease text:
        {text}

        For each problematic clause you find, provide:
        1. The exact clause text
        2. Why it's problematic
        3. The severity (high, medium, low)
        4. Plain English explanation
        5. Recommended action

        Format your response as JSON with this structure:
        {{
            "clauses": [
                {{
                    "clause_text": "exact text from lease",
                    "issue": "brief description of the problem",
                    "severity": "high/medium/low",
                    "explanation": "plain English explanation",
                    "recommendation": "what the tenant should do"
                }}
            ]
        }}
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful tenant rights lawyer."},
                    {"role": "user", "content": prompt.format(text=text_chunk)}
                ],
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            
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
    
    async def _extract_tenant_rights(self, text_chunk: str) -> List[TenantRight]:
        """
        Extract tenant rights and obligations from the lease text
        """
        prompt = """
        Analyze this lease text and extract the key tenant rights and obligations.

        Lease text:
        {text}

        Identify:
        1. Rights the tenant has
        2. Obligations the tenant must fulfill
        3. Important deadlines or procedures

        Format as JSON:
        {{
            "rights": [
                {{
                    "title": "Right name",
                    "description": "What this right means",
                    "importance": "high/medium/low"
                }}
            ]
        }}
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a tenant rights expert."},
                    {"role": "user", "content": prompt.format(text=text_chunk)}
                ],
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            
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
    
    async def _generate_plain_english_summary(self, document_text: str) -> str:
        """
        Generate a plain English summary of the lease document
        """
        prompt = """
        You are helping low-income renters understand their lease agreements. 
        Summarize this lease document in plain, simple English that a 6th grader could understand.

        Focus on:
        - Key terms and conditions
        - Important dates and deadlines  
        - What the tenant needs to know
        - Any red flags or concerns

        Keep it under 300 words and use simple language.

        Lease document:
        {text}
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful legal assistant who explains things simply."},
                    {"role": "user", "content": prompt.format(text=document_text[:4000])}  # Limit text length
                ],
                temperature=0.5
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    async def _generate_recommendations(self, unfair_clauses: List[ClauseAnalysis]) -> List[str]:
        """
        Generate actionable recommendations based on identified issues
        """
        if not unfair_clauses:
            return ["Your lease appears to be fairly standard. Review it carefully and keep a copy for your records."]
        
        high_severity = [c for c in unfair_clauses if c.severity == "high"]
        medium_severity = [c for c in unfair_clauses if c.severity == "medium"]
        
        recommendations = []
        
        if high_severity:
            recommendations.append("🚨 URGENT: This lease contains potentially illegal clauses. Consider consulting with a tenant rights organization or legal aid before signing.")
        
        if len(unfair_clauses) >= 3:
            recommendations.append("⚠️ Multiple concerning clauses found. Document everything and consider negotiating with your landlord.")
        
        recommendations.extend([
            "📋 Keep detailed records of all communications with your landlord",
            "📞 Know your local tenant rights hotline number",
            "💰 Understand your security deposit rights",
            "🏠 Take photos of the property condition before moving in"
        ])
        
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
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful legal expert who explains complex terms simply."},
                    {"role": "user", "content": prompt.format(clause=clause_text)}
                ],
                temperature=0.4
            )
            
            return response.choices[0].message.content
            
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