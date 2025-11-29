import numpy as np
import cv2
from pdf2image import convert_from_bytes
from io import BytesIO
from PIL import Image
import logging

logger = logging.getLogger(__name__)

def process_document(file_content: bytes, filename: str = "doc.pdf") -> list[np.ndarray]:
    logger.info("Processing document to images...")
    images = []
    try:
        if file_content.startswith(b"%PDF"):
            pil_images = convert_from_bytes(file_content, fmt="jpeg", dpi=150)
            for p_img in pil_images:
                images.append(np.array(p_img))
        else:
            image = Image.open(BytesIO(file_content)).convert("RGB")
            images.append(np.array(image))

        return [cv2.cvtColor(img, cv2.COLOR_RGB2BGR) for img in images]

    except Exception as e:
        logger.error(f"Image Processing Error: {e}")
        raise ValueError("Invalid file format")
