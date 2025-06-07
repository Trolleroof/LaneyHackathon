import os
import io
from typing import Optional
import pytesseract
from PIL import Image
import pdf2image
import cv2
import numpy as np

class OCRService:
    def __init__(self):
        # Configure Tesseract path if needed (for Mac with Homebrew)
        # Uncomment if you have issues finding Tesseract
        # pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'
        pass
    
    async def extract_text(self, file_content: bytes, content_type: str) -> str:
        """
        Extract text from uploaded document using OCR
        """
        try:
            if content_type == 'application/pdf':
                return await self._extract_from_pdf(file_content)
            elif content_type.startswith('image/'):
                return await self._extract_from_image(file_content)
            else:
                raise ValueError(f"Unsupported file type: {content_type}")
        
        except Exception as e:
            raise Exception(f"OCR extraction failed: {str(e)}")
    
    async def _extract_from_pdf(self, pdf_content: bytes) -> str:
        """Extract text from PDF using pdf2image and Tesseract"""
        try:
            # Convert PDF to images
            images = pdf2image.convert_from_bytes(
                pdf_content,
                dpi=300,  # High DPI for better OCR accuracy
                fmt='PNG'
            )
            
            extracted_text = ""
            
            for i, image in enumerate(images):
                # Preprocess image for better OCR
                processed_image = self._preprocess_image(image)
                
                # Extract text using Tesseract
                page_text = pytesseract.image_to_string(
                    processed_image,
                    config='--psm 6 -l eng'  # Page segmentation mode 6, English
                )
                
                extracted_text += f"\n--- Page {i+1} ---\n{page_text}\n"
            
            return extracted_text.strip()
            
        except Exception as e:
            raise Exception(f"PDF OCR failed: {str(e)}")
    
    async def _extract_from_image(self, image_content: bytes) -> str:
        """Extract text from image using Tesseract"""
        try:
            # Load image
            image = Image.open(io.BytesIO(image_content))
            
            # Preprocess image
            processed_image = self._preprocess_image(image)
            
            # Extract text
            text = pytesseract.image_to_string(
                processed_image,
                config='--psm 6 -l eng'
            )
            
            return text.strip()
            
        except Exception as e:
            raise Exception(f"Image OCR failed: {str(e)}")
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image to improve OCR accuracy
        """
        try:
            # Convert PIL image to OpenCV format
            open_cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply noise reduction
            denoised = cv2.medianBlur(gray, 3)
            
            # Apply adaptive thresholding for better text contrast
            thresh = cv2.adaptiveThreshold(
                denoised, 
                255, 
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 
                11, 
                2
            )
            
            # Convert back to PIL Image
            processed_image = Image.fromarray(thresh)
            
            return processed_image
            
        except Exception as e:
            # If preprocessing fails, return original image
            print(f"Image preprocessing failed: {str(e)}")
            return image
    
    def validate_extracted_text(self, text: str) -> bool:
        """
        Validate that extracted text contains meaningful content
        """
        if not text or len(text.strip()) < 50:
            return False
        
        # Check for common lease document keywords
        lease_keywords = [
            'lease', 'tenant', 'landlord', 'rent', 'property', 
            'agreement', 'monthly', 'deposit', 'premises'
        ]
        
        text_lower = text.lower()
        keyword_count = sum(1 for keyword in lease_keywords if keyword in text_lower)
        
        return keyword_count >= 2 