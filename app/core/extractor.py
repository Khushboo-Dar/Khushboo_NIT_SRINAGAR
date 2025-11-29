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

logger = logging.getLogger(__name__)
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
MODEL_NAME = "gemini-1.5-flash-001"

def clean_json_string(json_str: str) -> str:
    json_str = re.sub(r"```json\s*", "", json_str)
    json_str = re.sub(r"```", "", json_str)
    return json_str.strip()

def extract_data_from_images(opencv_images: list[np.ndarray]) -> tuple[dict, TokenUsage]:
    logger.info(f"Processing {len(opencv_images)} pages...")

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

    pil_images = []
    for img in opencv_images:
        pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        pil_img.thumbnail((1024, 1024))
        pil_images.append(pil_img)

    prompt = """
    Extract medical bill line items. Return JSON only.
    Keys: pagewise_line_items, page_no, page_type, bill_items, item_name, item_amount, item_rate, item_quantity.
    """

    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content([prompt, *pil_images])

        token_stats = TokenUsage(total_tokens=0, input_tokens=0, output_tokens=0)
        if hasattr(response, "usage_metadata"):
            token_stats = TokenUsage(
                total_tokens=response.usage_metadata.total_token_count,
                input_tokens=response.usage_metadata.prompt_token_count,
                output_tokens=response.usage_metadata.candidates_token_count
            )

        cleaned = clean_json_string(response.text)
        if cleaned.startswith("["):
            data = {"pagewise_line_items": json.loads(cleaned)}
        else:
            data = json.loads(cleaned)

        return data, token_stats

    except Exception as e:
        error_message = f"API FAILURE: {e}"
        logger.error(error_message)
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
