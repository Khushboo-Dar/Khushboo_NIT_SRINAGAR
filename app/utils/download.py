import requests
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

def download_file(url: str) -> bytes:
    logger.info(f"Downloading document from: {url}")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code != 200:
            logger.error(f"Download failed with status: {response.status_code}")
            raise HTTPException(status_code=400, detail=f"Failed to download file. Status: {response.status_code}")

        return response.content

    except Exception as e:
        logger.error(f"Download Error: {e}")
        raise HTTPException(status_code=400, detail=f"Download Error: {str(e)}")
