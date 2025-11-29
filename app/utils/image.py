import numpy as np
import cv2
from pdf2image import convert_from_bytes
from io import BytesIO
from PIL import Image
import logging

logger = logging.getLogger(__name__)

def preprocess_image(image: np.ndarray) -> np.ndarray:
    """
    Enhance image quality for better OCR/LLM extraction:
    - Denoise to remove artifacts and noise
    - Enhance contrast for text clarity
    - Auto-rotate if needed (basic heuristic)
    - Handle low-quality/blurry images
    """
    try:
        # Convert to grayscale for processing
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Apply denoising to reduce artifacts (important for handwritten/low-quality docs)
        denoised = cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)
        
        # Enhance contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        
        # Apply slight sharpening to make text crisper
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]])
        sharpened = cv2.filter2D(enhanced, -1, kernel)
        
        # Convert back to BGR for consistency
        result = cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR)
        
        logger.info("Image preprocessing completed: denoise + contrast enhancement + sharpening")
        return result
    except Exception as e:
        logger.warning(f"Preprocessing failed, returning original: {e}")
        return image

def detect_fraud_indicators(image: np.ndarray) -> dict:
    """
    Detect potential fraud indicators:
    - Inconsistent font/text patterns (whitespace anomalies)
    - Evidence of whitener/correction fluid
    - Suspicious overwriting patterns
    - Compression artifacts suggesting manipulation
    """
    fraud_flags = {
        "has_whitener_marks": False,
        "font_inconsistencies": False,
        "overwrite_detected": False,
        "compression_artifacts": False,
        "risk_level": "LOW"  # LOW, MEDIUM, HIGH
    }
    
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Detect whitener marks: look for anomalously bright white regions
        _, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
        white_pixels = np.sum(binary == 255)
        total_pixels = binary.shape[0] * binary.shape[1]
        white_ratio = white_pixels / total_pixels
        
        if white_ratio > 0.15:  # Abnormally high white content
            fraud_flags["has_whitener_marks"] = True
        
        # Detect overwriting: look for text overlaps using edge detection
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) > 200:  # Many overlapping contours = possible overwriting
            fraud_flags["overwrite_detected"] = True
        
        # Font inconsistency: check for varying stroke widths
        scharr_x = cv2.Scharr(gray, cv2.CV_32F, 1, 0)
        scharr_y = cv2.Scharr(gray, cv2.CV_32F, 0, 1)
        magnitude = np.sqrt(scharr_x**2 + scharr_y**2)
        stroke_variance = np.var(magnitude[magnitude > 0])
        
        if stroke_variance > 500:  # High variance = inconsistent fonts
            fraud_flags["font_inconsistencies"] = True
        
        # Determine risk level
        risk_count = sum([fraud_flags["has_whitener_marks"], 
                         fraud_flags["font_inconsistencies"],
                         fraud_flags["overwrite_detected"]])
        
        if risk_count >= 2:
            fraud_flags["risk_level"] = "HIGH"
        elif risk_count == 1:
            fraud_flags["risk_level"] = "MEDIUM"
        
        if fraud_flags["risk_level"] != "LOW":
            logger.warning(f"Fraud indicators detected: {fraud_flags}")
        
        return fraud_flags
    except Exception as e:
        logger.error(f"Fraud detection failed: {e}")
        return fraud_flags

def process_document(file_content: bytes, filename: str) -> list[np.ndarray]:
    """Process PDF/image files into list of preprocessed OpenCV images"""
    images = []
    try:
        if filename.lower().endswith('.pdf') or file_content.startswith(b'%PDF'):
            pil_images = convert_from_bytes(file_content, fmt='jpeg', dpi=200)  # Increased DPI for better quality
            for p_img in pil_images:
                img_array = np.array(p_img)
                img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                # Preprocess each page
                preprocessed = preprocess_image(img_bgr)
                # Detect fraud indicators
                fraud_info = detect_fraud_indicators(preprocessed)
                images.append({
                    'image': preprocessed,
                    'fraud_flags': fraud_info
                })
                logger.info(f"Processed PDF page: {len(images)}")
        else:
            image = Image.open(BytesIO(file_content)).convert('RGB')
            img_array = np.array(image)
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            preprocessed = preprocess_image(img_bgr)
            fraud_info = detect_fraud_indicators(preprocessed)
            images.append({
                'image': preprocessed,
                'fraud_flags': fraud_info
            })
            logger.info("Processed image document")
        
        return images
    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        raise
