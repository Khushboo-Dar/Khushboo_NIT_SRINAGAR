import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
import cv2
import numpy as np
from app.models.schemas import TokenUsage
import logging
import typing_extensions as typing

logger = logging.getLogger(__name__)
load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "gemini-1.5-flash"

class BillItem(typing.TypedDict):
    item_name: str
    item_amount: float
    item_rate: float
    item_quantity: float

class PageItem(typing.TypedDict):
    page_no: str
    page_type: str
    bill_items: list[BillItem]

class BillResponse(typing.TypedDict):
    pagewise_line_items: list[PageItem]

def extract_data_from_images(opencv_images: list[np.ndarray]) -> tuple[dict, TokenUsage]:
    logger.info(f"Sending {len(opencv_images)} pages to {MODEL_NAME}...")

    pil_images = []
    for img in opencv_images:
        pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        pil_img.thumbnail((1024, 1024))
        pil_images.append(pil_img)

    generation_config = genai.GenerationConfig(
        response_mime_type="application/json",
        response_schema=BillResponse,
        temperature=0.1
    )

    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        generation_config=generation_config
    )

    prompt = """
    Extract medical bill line items.
    Ignore totals, keep repeated rows, infer missing values.
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
        return parsed_data, token_stats

    except Exception as e:
        logger.error(f"Gemini Extraction Failed: {e}")
        return {"pagewise_line_items": []}, TokenUsage(total_tokens=0, input_tokens=0, output_tokens=0)
