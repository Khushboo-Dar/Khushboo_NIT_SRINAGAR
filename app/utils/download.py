import requests
from fastapi import HTTPException

def download_file(url: str) -> bytes:
    try:
        if "localhost" in url or "127.0.0.1" in url:
            pass

        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.content

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Download Failed: {str(e)}")
