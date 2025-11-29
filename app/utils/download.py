import requests
from fastapi import HTTPException
import logging
import time

logger = logging.getLogger(__name__)

def download_file(url: str, max_retries: int = 3, timeout: int = 30) -> bytes:
    """
    Download file from URL with retry logic and enhanced error handling.
    
    Args:
        url: URL to download from
        max_retries: Number of retry attempts
        timeout: Request timeout in seconds
    
    Returns:
        bytes: Downloaded file content
    
    Raises:
        HTTPException: If download fails after retries
    """
    if not url or not isinstance(url, str):
        logger.error(f"Invalid URL: {url}")
        raise HTTPException(status_code=400, detail="Invalid document URL provided")
    
    logger.info(f"Attempting to download from: {url[:80]}...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Download attempt {attempt}/{max_retries}...")
            response = requests.get(url, headers=headers, timeout=timeout)
            
            if response.status_code == 403:
                logger.error(f"403 Forbidden - check if URL is still valid or expired")
                raise HTTPException(
                    status_code=400,
                    detail="Document URL is forbidden or expired. Please check the URL."
                )
            
            if response.status_code == 404:
                logger.error(f"404 Not Found - document does not exist")
                raise HTTPException(
                    status_code=400,
                    detail="Document not found at the provided URL"
                )
            
            response.raise_for_status()
            
            content_length = len(response.content)
            logger.info(f"✓ Successfully downloaded {content_length} bytes")
            
            return response.content
        
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout on attempt {attempt}/{max_retries}")
            if attempt == max_retries:
                raise HTTPException(
                    status_code=408,
                    detail="Download timeout - server took too long to respond"
                )
            time.sleep(2 ** attempt)  # Exponential backoff
        
        except requests.exceptions.ConnectionError as ce:
            logger.warning(f"Connection error on attempt {attempt}/{max_retries}: {ce}")
            if attempt == max_retries:
                raise HTTPException(
                    status_code=503,
                    detail="Connection error - unable to reach the document URL"
                )
            time.sleep(2 ** attempt)
        
        except requests.exceptions.RequestException as re:
            logger.warning(f"Request error on attempt {attempt}/{max_retries}: {re}")
            if attempt == max_retries:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to download document: {str(re)}"
                )
            time.sleep(2 ** attempt)
    
    raise HTTPException(
        status_code=500,
        detail="Failed to download document after multiple retries"
    )
