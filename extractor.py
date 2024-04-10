# extractor.py
from fastapi import APIRouter


from fastapi import UploadFile, File
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class ExtractData(BaseModel):
    data: Optional[str] = None
    pdf: Optional[UploadFile] = File(None)

@router.post("/extract")
async def extract_data(extract_data: ExtractData):
    # Your extraction logic here
    return {"data": extract_data.data, "pdf": extract_data.pdf.filename}
