import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
import cv2
import numpy as np
from app.models.schemas import TokenUsage
import logging

logger = logging.getLogger(__name__)
load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "gemini-2.5-flash"

def extract_data_from_images(opencv_images: list[np.ndarray]) -> tuple[dict, TokenUsage]:
    logger.info(f"Sending {len(opencv_images)} pages to {MODEL_NAME}...")

    generation_config = {
        "temperature": 0.0,
        "response_mime_type": "application/json"
    }

    try:
        model = genai.GenerativeModel(model_name=MODEL_NAME, generation_config=generation_config)
    except Exception as e:
        logger.error(f"Failed to load model {MODEL_NAME}. Error: {e}")
        return {"pagewise_line_items": []}, TokenUsage(total_tokens=0, input_tokens=0, output_tokens=0)

    pil_images = []
    for img in opencv_images:
        pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        pil_img.thumbnail((1024, 1024))
        pil_images.append(pil_img)

    prompt = """
    You are an expert medical bill auditor. Extract individual line items.
    Classify pages as Bill Detail, Final Bill, or Pharmacy.
    Extract all chargeable rows, ignore total-like rows, keep duplicates.
    Default Qty=1, infer rate or amount if missing.
    """

    try:
        response = model.generate_content([prompt, *pil_images])

        if hasattr(response, "usage_metadata"):
            usage = response.usage_metadata
            token_stats = TokenUsage(
                total_tokens=usage.total_token_count,
                input_tokens=usage.prompt_token_count,
                output_tokens=usage.candidates_token_count
            )
        else:
            token_stats = TokenUsage(total_tokens=0, input_tokens=0, output_tokens=0)

        parsed_data = json.loads(response.text)
        if isinstance(parsed_data, list):
            parsed_data = {"pagewise_line_items": parsed_data}

        return parsed_data, token_stats

    except Exception as e:
        logger.error(f"Gemini Extraction Failed: {e}")
        return {"pagewise_line_items": []}, TokenUsage(total_tokens=0, input_tokens=0, output_tokens=0)
