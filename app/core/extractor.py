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
        "temperature": 0.1,
        "response_mime_type": "application/json"
    }

    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        generation_config=generation_config
    )

    pil_images = [Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)) for img in opencv_images]

    prompt = """
    You are an expert medical bill auditor. Extract strictly individual line items.

    ### 1. PAGE CLASSIFICATION:
    Classify 'page_type' for every page:
    - "Pharmacy": Lists drug names, batches, expiry dates.
    - "Bill Detail": Daily charges, room rent, specific lab tests, nursing charges.
    - "Final Bill": Summary pages with high-level categories (e.g. "Total Pharmacy").

    ### 2. EXTRACTION RULES (CRITICAL):
    - **Granularity**: Extract EVERY single chargeable item row.
    - **Ignore Aggregates**: DO NOT extract rows labeled "SubTotal", "Category Total", "Group Total".
    - **Repetitive Items**: If "Blood Sugar" appears 10 times, extract all 10.
    - **Missing Data**:
       * Qty missing -> 1
       * Rate missing -> Item Amount
       * Amount missing -> Rate * Qty

    ### 3. OUTPUT SCHEMA:
    {
        "pagewise_line_items": [
            {
                "page_no": "1",
                "page_type": "Pharmacy",
                "bill_items": [
                    {
                        "item_name": "Paracetamol",
                        "item_amount": 10.0,
                        "item_rate": 5.0,
                        "item_quantity": 2.0
                    }
                ]
            }
        ]
    }
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
