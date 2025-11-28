import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
import cv2
import numpy as np
from app.models.schemas import TokenUsage

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "gemini-2.5-flash"

def extract_data_from_images(opencv_images: list[np.ndarray]) -> tuple[dict, TokenUsage]:
    generation_config = {
        "temperature": 0.0,
        "response_mime_type": "application/json"
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
    You are an expert medical data auditor. Extract strictly individual line items.

    ### 1. PAGE CLASSIFICATION RULES:
    Classify page_type for every page:
    - Pharmacy for drugs and expiry dates.
    - Bill Detail for daily hospital charges.
    - Final Bill for summary pages.

    ### 2. EXTRACTION RULES:
    - Extract every chargeable line item.
    - Ignore SubTotal or Total-type rows.
    - Repeat items individually if repeated.
    - Qty missing -> 1, Rate missing -> Item Amount.
    """

    try:
        response = model.generate_content([prompt, *pil_images])

        usage = response.usage_metadata
        token_stats = TokenUsage(
            total_tokens=usage.total_token_count,
            input_tokens=usage.prompt_token_count,
            output_tokens=usage.candidates_token_count
        )

        return json.loads(response.text), token_stats

    except Exception as e:
        print(f"Gemini Error: {e}")
        return {"pagewise_line_items": []}, TokenUsage(total_tokens=0, input_tokens=0, output_tokens=0)
