from botocore.exceptions import ClientError
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.pipeline.transcribe import transcribe


router = APIRouter(prefix="/recordings", tags=["recordings"])



class TranscribeRequest(BaseModel):
    s3_key: str



@router.post("/transcribe")
async def transcribe_recording(body: TranscribeRequest) -> dict:
    s3_key = body.s3_key
    """Transcribe an already-uploaded recording (by its s3 key), word-level, synchronously."""
    try:
        return transcribe(s3_key)
    except ClientError as e:
        # object missing / no access -> treat as a bad key from the caller
        if e.response.get("Error", {}).get("Code") in {"404", "NoSuchKey"}:
            raise HTTPException(status_code=404, detail=f"No recording found for key: {s3_key}")
        raise
