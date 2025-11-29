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

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "gemini-1.5-flash"

def clean_json_string(json_str: str) -> str:
    json_str = re.sub(r"```json\s*", "", json_str)
    json_str = re.sub(r"```", "", json_str)
    json_str = json_str.strip()

    start_idx = json_str.find("{")
    list_idx = json_str.find("[")
    if (list_idx != -1 and list_idx < start_idx) or start_idx == -1:
        start_idx = list_idx
        end_idx = json_str.rfind("]") + 1
    else:
        end_idx = json_str.rfind("}") + 1

    if start_idx != -1 and end_idx != -1:
        return json_str[start_idx:end_idx]

    return json_str

def extract_data_from_images(opencv_images: list[np.ndarray]) -> tuple[dict, TokenUsage]:
    logger.info(f"Sending {len(opencv_images)} pages to {MODEL_NAME}...")

    generation_config = {
        "temperature": 0.1
    }

    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        generation_config=generation_config
    )

    pil_images = []
    for img in opencv_images:
        pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        pil_img.thumbnail((1024, 1024))
        pil_images.append(pil_img)

    prompt = """
    Extract medical bill data into JSON.
    page_type one of Bill Detail, Final Bill, Pharmacy.
    Ignore totals and category headers.
    Default Qty=1, compute missing amount.
    """

    try:
        response = model.generate_content([prompt, *pil_images])
        raw_text = response.text

        if hasattr(response, "usage_metadata"):
            usage = response.usage_metadata
            token_stats = TokenUsage(
                total_tokens=usage.total_token_count,
                input_tokens=usage.prompt_token_count,
                output_tokens=usage.candidates_token_count
            )
        else:
            token_stats = TokenUsage(total_tokens=0, input_tokens=0, output_tokens=0)

        cleaned_text = clean_json_string(raw_text)
        try:
            parsed_data = json.loads(cleaned_text)
        except json.JSONDecodeError:
            return {"pagewise_line_items": []}, token_stats

        if isinstance(parsed_data, list):
            parsed_data = {"pagewise_line_items": parsed_data}

        if "pagewise_line_items" not in parsed_data:
            if "bill_items" in parsed_data:
                parsed_data = {
                    "pagewise_line_items": [
                        {"page_no": "1", "page_type": "Unknown", "bill_items": parsed_data["bill_items"]}
                    ]
                }
            else:
                parsed_data["pagewise_line_items"] = []

        return parsed_data, token_stats

    except Exception as e:
        logger.error(f"Gemini Extraction Critical Failure: {e}")
        return {"pagewise_line_items": []}, TokenUsage(total_tokens=0, input_tokens=0, output_tokens=0)
