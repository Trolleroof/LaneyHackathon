import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import google.generativeai as genai
from models.schemas import LetterType, TenantInfo, LandlordInfo

class LetterService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key and api_key != "your_gemini_api_key_here":
            genai.configure(api_key=api_key)
            self.gemini_client = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.gemini_client = None
        # In-memory storage for development
        self.letters = {}
        self.next_id = 1
    
    async def generate_letter(
        self,
        letter_type: LetterType,
        context: str,
        tenant_info: TenantInfo,
        landlord_info: LandlordInfo,
        specific_issues: List[str],
        language: str = "en"
    ) -> str:
        """
        Generate a formal letter based on the specified type and context
        """
        try:
            # Get the appropriate template and prompt
            prompt = self._get_letter_prompt(letter_type, language)
            
            # Format the prompt with user information
            formatted_prompt = prompt.format(
                tenant_name=tenant_info.name,
                tenant_address=tenant_info.address,
                tenant_phone=tenant_info.phone or "N/A",
                tenant_email=tenant_info.email or "N/A",
                landlord_name=landlord_info.name,
                landlord_address=landlord_info.address or "N/A",
                landlord_phone=landlord_info.phone or "N/A",
                landlord_email=landlord_info.email or "N/A",
                company_name=landlord_info.company_name or landlord_info.name,
                context=context,
                specific_issues="\n".join(f"• {issue}" for issue in specific_issues),
                date=datetime.now().strftime("%B %d, %Y")
            )
            
            # Generate letter using Gemini
            if not self.gemini_client:
                return "Demo letter: Please set your Gemini API key to generate professional letters to your landlord."
            
            # Language instructions
            language_instructions = {
                "en": "Write the letter in English",
                "es": "Escribe la carta en español",
                "fr": "Rédigez la lettre en français", 
                "de": "Schreiben Sie den Brief auf Deutsch",
                "it": "Scrivi la lettera in italiano",
                "pt": "Escreva a carta em português",
                "zh": "用中文写信",
                "ja": "日本語で手紙を書いてください",
                "ko": "한국어로 편지를 써주세요",
                "ar": "اكتب الرسالة باللغة العربية"
            }
            
            lang_instruction = language_instructions.get(language, "Write the letter in English")
            
            response = self.gemini_client.generate_content(
                f"You are a legal assistant helping tenants write professional, formal letters to their landlords. Write clear, polite but firm letters that protect tenant rights.\n\nIMPORTANT: {lang_instruction}. The entire letter must be in the requested language.\n\n{formatted_prompt}",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=2048,
                )
            )
            
            generated_letter = response.text
            return generated_letter
            
        except Exception as e:
            raise Exception(f"Letter generation failed: {str(e)}")
    
    def _get_letter_prompt(self, letter_type: LetterType, language: str = "en") -> str:
        """
        Get the appropriate prompt template for each letter type
        """
        # Language instructions
        language_instructions = {
            "en": "Write the letter in English",
            "es": "Escribe la carta en español",
            "fr": "Rédigez la lettre en français", 
            "de": "Schreiben Sie den Brief auf Deutsch",
            "it": "Scrivi la lettera in italiano",
            "pt": "Escreva a carta em português",
            "zh": "用中文写信",
            "ja": "日本語で手紙を書いてください",
            "ko": "한국어로 편지를 써주세요",
            "ar": "اكتب الرسالة باللغة العربية"
        }
        
        lang_instruction = language_instructions.get(language, "Write the letter in English")
        
        templates = {
            LetterType.REPAIR_REQUEST: """
IMPORTANT: """ + lang_instruction + """. The entire letter must be in the requested language.

Write a formal letter requesting repairs from a landlord. Use this information:

Date: {date}
Tenant: {tenant_name}
Tenant Address: {tenant_address}
Tenant Phone: {tenant_phone}
Tenant Email: {tenant_email}

Landlord: {landlord_name}
Company: {company_name}
Landlord Address: {landlord_address}

Context: {context}

Specific Issues:
{specific_issues}

The letter should:
- Be professional and respectful
- Clearly describe the repair issues
- Reference tenant rights regarding habitability
- Request a reasonable timeline for repairs
- Mention legal obligations if appropriate
- Include proper formatting with addresses and date
""",

            LetterType.RENT_DISPUTE: """
IMPORTANT: """ + lang_instruction + """. The entire letter must be in the requested language.

Write a formal letter regarding a rent dispute. Use this information:

Date: {date}
Tenant: {tenant_name}
Tenant Address: {tenant_address}
Tenant Phone: {tenant_phone}
Tenant Email: {tenant_email}

Landlord: {landlord_name}
Company: {company_name}
Landlord Address: {landlord_address}

Context: {context}

Specific Issues:
{specific_issues}

The letter should:
- Be professional and diplomatic
- Clearly explain the dispute
- Reference relevant lease terms
- Propose a reasonable solution
- Mention tenant rights regarding rent increases
- Request written response
- Include proper formatting with addresses and date
""",

            LetterType.SECURITY_DEPOSIT: """
IMPORTANT: """ + lang_instruction + """. The entire letter must be in the requested language.

Write a formal letter regarding security deposit return. Use this information:

Date: {date}
Tenant: {tenant_name}
Tenant Address: {tenant_address}
Tenant Phone: {tenant_phone}
Tenant Email: {tenant_email}

Landlord: {landlord_name}
Company: {company_name}
Landlord Address: {landlord_address}

Context: {context}

Specific Issues:
{specific_issues}

The letter should:
- Be professional and clear
- Reference move-out date and deposit amount
- Request itemized list of deductions
- Mention legal requirements for deposit return
- Specify timeline for response
- Include forwarding address for deposit return
- Include proper formatting with addresses and date
""",

            LetterType.NO_NOTICE_ENTRY: """
IMPORTANT: """ + lang_instruction + """. The entire letter must be in the requested language.

Write a formal letter regarding unauthorized entry by landlord. Use this information:

Date: {date}
Tenant: {tenant_name}
Tenant Address: {tenant_address}
Tenant Phone: {tenant_phone}
Tenant Email: {tenant_email}

Landlord: {landlord_name}
Company: {company_name}
Landlord Address: {landlord_address}

Context: {context}

Specific Issues:
{specific_issues}

The letter should:
- Be firm but professional
- Document the unauthorized entry incident(s)
- Reference tenant privacy rights
- Cite relevant laws about required notice
- Request compliance with proper notice procedures
- Warn of legal consequences for continued violations
- Include proper formatting with addresses and date
""",

            LetterType.NOISE_COMPLAINT: """
IMPORTANT: """ + lang_instruction + """. The entire letter must be in the requested language.

Write a formal letter about noise issues. Use this information:

Date: {date}
Tenant: {tenant_name}
Tenant Address: {tenant_address}
Tenant Phone: {tenant_phone}
Tenant Email: {tenant_email}

Landlord: {landlord_name}
Company: {company_name}
Landlord Address: {landlord_address}

Context: {context}

Specific Issues:
{specific_issues}

The letter should:
- Be respectful but clear about the problem
- Document specific instances with dates/times
- Reference lease terms about noise/disturbances
- Request landlord intervention
- Mention right to peaceful enjoyment
- Suggest reasonable solutions
- Include proper formatting with addresses and date
""",

            LetterType.LEASE_VIOLATION: """
IMPORTANT: """ + lang_instruction + """. The entire letter must be in the requested language.

Write a formal letter about landlord lease violations. Use this information:

Date: {date}
Tenant: {tenant_name}
Tenant Address: {tenant_address}
Tenant Phone: {tenant_phone}
Tenant Email: {tenant_email}

Landlord: {landlord_name}
Company: {company_name}
Landlord Address: {landlord_address}

Context: {context}

Specific Issues:
{specific_issues}

The letter should:
- Be professional and factual
- Cite specific lease provisions being violated
- Document the violations clearly
- Request immediate correction
- Reference legal consequences of continued violation
- Set reasonable timeline for compliance
- Include proper formatting with addresses and date
""",

            LetterType.DISCRIMINATION: """
IMPORTANT: """ + lang_instruction + """. The entire letter must be in the requested language.

Write a formal letter regarding housing discrimination. Use this information:

Date: {date}
Tenant: {tenant_name}
Tenant Address: {tenant_address}
Tenant Phone: {tenant_phone}
Tenant Email: {tenant_email}

Landlord: {landlord_name}
Company: {company_name}
Landlord Address: {landlord_address}

Context: {context}

Specific Issues:
{specific_issues}

The letter should:
- Be very professional and serious in tone
- Document discriminatory behavior with specific details
- Reference Fair Housing Act and local anti-discrimination laws
- Demand immediate cessation of discriminatory practices
- Mention intention to file complaints with authorities
- Request written response acknowledging the issue
- Include proper formatting with addresses and date
""",

            LetterType.HABITABILITY: """
IMPORTANT: """ + lang_instruction + """. The entire letter must be in the requested language.

Write a formal letter about habitability issues. Use this information:

Date: {date}
Tenant: {tenant_name}
Tenant Address: {tenant_address}
Tenant Phone: {tenant_phone}
Tenant Email: {tenant_email}

Landlord: {landlord_name}
Company: {company_name}
Landlord Address: {landlord_address}

Context: {context}

Specific Issues:
{specific_issues}

The letter should:
- Be serious and professional
- Detail all habitability problems clearly
- Reference implied warranty of habitability
- Set reasonable deadline for repairs
- Mention potential legal remedies (rent withholding, repair and deduct)
- Request written response with repair timeline
- Include proper formatting with addresses and date
""",

            LetterType.GENERAL_CONCERN: """
IMPORTANT: """ + lang_instruction + """. The entire letter must be in the requested language.

Write a formal letter addressing general concerns about lease terms or landlord practices. Use this information:

Date: {date}
Tenant: {tenant_name}
Tenant Address: {tenant_address}
Tenant Phone: {tenant_phone}
Tenant Email: {tenant_email}

Landlord: {landlord_name}
Company: {company_name}
Landlord Address: {landlord_address}

Context: {context}

Specific Issues:
{specific_issues}

The letter should:
- Be professional and respectful
- Clearly outline the concerns from the lease analysis
- Reference specific problematic clauses or practices
- Request clarification or modification of concerning terms
- Propose reasonable solutions where appropriate
- Reference tenant rights and fair housing practices
- Request written response addressing the concerns
- Include proper formatting with addresses and date
"""
        }
        
        return templates.get(letter_type, templates[LetterType.REPAIR_REQUEST])
    
    async def save_letter(
        self,
        user_id: int,
        letter_type: LetterType,
        content: str,
        db = None
    ) -> int:
        """
        Save generated letter to storage
        """
        try:
            letter_id = self.next_id
            self.next_id += 1
            
            letter_data = {
                "id": letter_id,
                "user_id": user_id,
                "letter_type": letter_type,
                "content": content,
                "created_at": datetime.now().isoformat()
            }
            
            self.letters[letter_id] = letter_data
            
            print(f"Saved letter with ID: {letter_id}")
            return letter_id
            
        except Exception as e:
            raise Exception(f"Failed to save letter: {str(e)}")
    
    async def get_user_letters(
        self,
        user_id: int,
        db = None
    ) -> List[Dict[str, Any]]:
        """
        Get all letters for a user
        """
        try:
            user_letters = [
                letter for letter in self.letters.values()
                if letter["user_id"] == user_id
            ]
            
            # Sort by creation date (newest first)
            user_letters.sort(
                key=lambda x: x["created_at"],
                reverse=True
            )
            
            return user_letters
            
        except Exception as e:
            print(f"Error retrieving letters for user {user_id}: {str(e)}")
            return []
    
    async def get_letter_by_id(
        self,
        letter_id: int,
        user_id: int,
        db = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific letter by ID
        """
        try:
            letter = self.letters.get(letter_id)
            
            if not letter:
                return None
            
            # Check if user owns this letter
            if letter["user_id"] != user_id:
                return None
            
            return letter
            
        except Exception as e:
            print(f"Error retrieving letter {letter_id}: {str(e)}")
            return None
    
    def get_letter_templates(self) -> Dict[str, str]:
        """
        Get available letter templates for the frontend
        """
        return {
            "repair_request": "Request repairs for property issues",
            "rent_dispute": "Dispute rent increases or charges",
            "security_deposit": "Request return of security deposit",
            "no_notice_entry": "Address unauthorized entry by landlord",
            "noise_complaint": "Report noise or disturbance issues",
            "lease_violation": "Address landlord lease violations",
            "discrimination": "Report housing discrimination",
            "habitability": "Address serious habitability problems"
        } 