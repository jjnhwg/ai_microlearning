from botocore.exceptions import ClientError
from fastapi import HTTPException
from pydantic import BaseModel

from backend.pipeline.transcribe import transcribe

# TODO (you): create the router -> router = APIRouter(prefix=..., tags=[...])
# TODO (you): add the route decorator + endpoint function (name it what you want).
#             have it take a TranscribeRequest body and return transcribe_recording(body.s3_key)


class TranscribeRequest(BaseModel):
    s3_key: str


def transcribe_recording(s3_key: str) -> dict:
    """Transcribe an already-uploaded recording (by its s3 key), word-level, synchronously."""
    try:
        return transcribe(s3_key)
    except ClientError as e:
        # object missing / no access -> treat as a bad key from the caller
        if e.response.get("Error", {}).get("Code") in {"404", "NoSuchKey"}:
            raise HTTPException(status_code=404, detail=f"No recording found for key: {s3_key}")
        raise
