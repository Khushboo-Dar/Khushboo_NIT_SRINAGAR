from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from app.utils.download import download_file
from app.utils.image import process_document
from app.core.extractor import extract_data_from_images
from app.core.calculator import reconcile_totals
from app.models.schemas import ExtractionResponse

app = FastAPI(title="Bajaj Datathon API")

class DocumentRequest(BaseModel):
    document: str

@app.post("/extract-bill-data", response_model=ExtractionResponse)
async def extract_bill_data(request: DocumentRequest):
    try:
        file_bytes = download_file(request.document)
        images = process_document(file_bytes, request.document)
        raw_json, token_stats = extract_data_from_images(images)
        processed_data = reconcile_totals(raw_json)

        return ExtractionResponse(
            is_success=True,
            token_usage=token_stats,
            data=processed_data
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
