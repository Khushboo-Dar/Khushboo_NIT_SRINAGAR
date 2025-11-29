from pydantic import BaseModel, Field
from typing import List, Literal

class TokenUsage(BaseModel):
    total_tokens: int
    input_tokens: int
    output_tokens: int

class BillItem(BaseModel):
    item_name: str = Field(..., description="Exactly as mentioned in the bill")
    item_amount: float = Field(..., description="Net Amount post discounts")
    item_rate: float = Field(..., description="Unit rate")
    item_quantity: float = Field(..., description="Quantity")

class PageWiseItems(BaseModel):
    page_no: str
    page_type: Literal["Bill Detail", "Final Bill", "Pharmacy", "Unknown"]
    bill_items: List[BillItem]

class ExtractionData(BaseModel):
    pagewise_line_items: List[PageWiseItems]
    total_item_count: int

class ExtractionResponse(BaseModel):
    is_success: bool
    token_usage: TokenUsage
    data: ExtractionData
