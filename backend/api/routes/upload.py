import os
import uuid

import boto3
from fastapi import APIRouter, HTTPException, UploadFile

# TODO (you): set your prefix and tags here
router = APIRouter(prefix="/recordings", tags=["recordings"])

_BUCKET = os.environ["SPEAKSHARP_S3_BUCKET"]
_s3 = boto3.client("s3") # way to interact with client 


_ALLOWED_CONTENT_TYPES = {
    "audio/mpeg", "audio/mp4", "audio/wav", "audio/x-wav",
    "audio/webm", "audio/ogg", "audio/flac",
    "audio/m4a", "audio/x-m4a",
}

@router.post("/upload")
async def upload_recording(audio: UploadFile) -> dict:
    if audio.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail=f"Unsupported media type: {audio.content_type}")

    # generate a unique S3 key for the uploaded file
    ext = os.path.splitext(audio.filename or "")[-1].lstrip(".")[:8]

    #generates a unique name for the S3 object based on UUIDs
    key = f"recordings/{uuid.uuid4()}/{uuid.uuid4()}.{ext}" if ext else f"recordings/{uuid.uuid4()}/audio"

    _s3.upload_fileobj(audio.file, _BUCKET, key)
    return {"s3_key": key, "bucket": _BUCKET}
