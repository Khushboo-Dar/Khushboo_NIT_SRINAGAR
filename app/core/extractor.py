import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
import cv2
import numpy as np
from app.models.schemas import TokenUsage
import logging
import re
from io import BytesIO

logger = logging.getLogger(__name__)
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
MODEL_NAME = "gemini-2.5-flash"

def clean_json_string(json_str: str) -> str:
    """Remove markdown formatting from JSON strings"""
    json_str = re.sub(r"```json\s*", "", json_str)
    json_str = re.sub(r"```", "", json_str)
    return json_str.strip()

def extract_data_from_images(processed_images: list) -> tuple[dict, TokenUsage]:
    """
    Extract bill line items from images using Gemini 2.5 Flash with enhanced prompting.
    
    Args:
        processed_images: List of dicts with 'image' and 'fraud_flags' keys
    
    Returns:
        tuple: (extracted_data_dict, TokenUsage)
    """
    logger.info(f"Processing {len(processed_images)} pages...")

    if not api_key:
        error_msg = "CRITICAL ERROR: GEMINI_API_KEY is missing in environment variables"
        return {
            "pagewise_line_items": [{
                "page_no": "0",
                "page_type": "Unknown",
                "bill_items": [{
                    "item_name": error_msg,
                    "item_amount": 0,
                    "item_rate": 0,
                    "item_quantity": 0
                }]
            }]
        }, TokenUsage(total_tokens=0, input_tokens=0, output_tokens=0)

    # Convert images to PIL format for Gemini
    pil_images = []
    fraud_warnings = []
    
    for idx, processed in enumerate(processed_images, 1):
        img_array = processed['image']
        pil_img = Image.fromarray(cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB))
        pil_img.thumbnail((1024, 1024))
        pil_images.append(pil_img)
        
        # Log fraud indicators
        fraud_flags = processed.get('fraud_flags', {})
        if fraud_flags.get('risk_level') != 'LOW':
            fraud_warnings.append(f"Page {idx}: {fraud_flags}")
            logger.warning(f"Potential fraud on page {idx}: {fraud_flags}")

    # Enhanced prompt with detailed instructions
    prompt = """
You are an expert bill/invoice data extraction specialist. Extract ALL line items from the medical/healthcare bill images provided.

CRITICAL INSTRUCTIONS:
1. Extract EVERY line item visible on the bill - do NOT skip any items
2. Include item name, quantity, rate, and amount EXACTLY as shown in the bill
3. Do NOT double-count items (e.g., don't list items both in details and summary)
4. For multi-page bills, identify page type: "Bill Detail" (main bill), "Final Bill" (summary page), or "Pharmacy" (pharmacy charges)
5. If an item amount is missing but quantity and rate exist, calculate: amount = quantity × rate
6. Preserve exact formatting of item names as they appear in the bill
7. Return ONLY valid JSON, no markdown formatting

Return JSON with this exact structure:
{
    "pagewise_line_items": [
        {
            "page_no": "1",
            "page_type": "Bill Detail",
            "bill_items": [
                {
                    "item_name": "Consultation Charge",
                    "item_quantity": 1,
                    "item_rate": 500.00,
                    "item_amount": 500.00
                }
            ]
        }
    ]
}

VALIDATION CHECKLIST:
- ✓ Every line item from the bill is included
- ✓ No duplicate entries
- ✓ Amounts match the bill exactly
- ✓ Format is valid JSON only (no markdown)
- ✓ All fields (item_name, item_quantity, item_rate, item_amount) are present
"""

    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content([prompt] + pil_images, stream=False)

        # Extract token usage
        token_stats = TokenUsage(total_tokens=0, input_tokens=0, output_tokens=0)
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            token_stats = TokenUsage(
                total_tokens=getattr(response.usage_metadata, "total_token_count", 0),
                input_tokens=getattr(response.usage_metadata, "prompt_token_count", 0),
                output_tokens=getattr(response.usage_metadata, "candidates_token_count", 0)
            )
            logger.info(f"Token usage: {token_stats}")

        # Parse response
        cleaned = clean_json_string(response.text)
        
        try:
            if cleaned.startswith("["):
                data = {"pagewise_line_items": json.loads(cleaned)}
            else:
                data = json.loads(cleaned)
        except json.JSONDecodeError as je:
            logger.error(f"JSON parsing failed: {je}")
            logger.error(f"Response text: {cleaned[:500]}")
            raise ValueError(f"Invalid JSON response from model: {str(je)}")

        # Add fraud warnings to data if present
        if fraud_warnings:
            data["fraud_warnings"] = fraud_warnings
            logger.warning(f"Fraud warnings for submission: {fraud_warnings}")

        return data, token_stats

    except Exception as e:
        error_message = f"API FAILURE: {e}"
        logger.error(error_message, exc_info=True)
        return {
            "pagewise_line_items": [{
                "page_no": "1",
                "page_type": "Unknown",
                "bill_items": [{
                    "item_name": error_message,
                    "item_amount": 0.0,
                    "item_rate": 0.0,
                    "item_quantity": 0.0
                }]
            }]
        }, TokenUsage(total_tokens=0, input_tokens=0, output_tokens=0)
