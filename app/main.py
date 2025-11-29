from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import logging
from app.utils.download import download_file
from app.utils.image import process_document
from app.core.extractor import extract_data_from_images
from app.core.calculator import reconcile_totals
from app.models.schemas import ExtractionResponse

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Bajaj Datathon Bill Extraction API",
    description="Advanced bill extraction with fraud detection and image preprocessing",
    version="1.0.0"
)

class DocumentRequest(BaseModel):
    document: str = "URL to the bill document (PDF or image)"

@app.post("/extract-bill-data", response_model=ExtractionResponse)
async def extract_bill_data(request: DocumentRequest):
    """
    Extract line items from a bill document.
    
    Args:
        request: DocumentRequest with 'document' URL
    
    Returns:
        ExtractionResponse with extracted data, token usage, and success status
    """
    try:
        logger.info(f"Received request for document: {request.document[:50]}...")
        
        # Step 1: Download document
        logger.info("Step 1: Downloading document...")
        file_bytes = download_file(request.document)
        logger.info(f"Downloaded {len(file_bytes)} bytes")
        
        # Step 2: Process document (preprocess + fraud detection)
        logger.info("Step 2: Processing document (preprocessing & fraud detection)...")
        processed_images = process_document(file_bytes, request.document)
        logger.info(f"Processed {len(processed_images)} pages")
        
        # Step 3: Extract data using LLM
        logger.info("Step 3: Extracting bill data using LLM...")
        raw_json, token_stats = extract_data_from_images(processed_images)
        logger.info(f"Extraction complete. Tokens used: {token_stats.total_tokens}")
        
        # Step 4: Reconcile and validate totals
        logger.info("Step 4: Reconciling totals and validating data...")
        processed_data = reconcile_totals(raw_json)
        logger.info(f"Total items extracted: {processed_data.total_item_count}")
        
        response = ExtractionResponse(
            is_success=True,
            token_usage=token_stats,
            data=processed_data
        )
        
        logger.info("✓ Request completed successfully")
        return response

    except HTTPException as http_err:
        logger.error(f"HTTP Error: {http_err.detail}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Bill extraction failed: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Bajaj Datathon Bill Extraction API"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
