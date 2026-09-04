"""Feedback report endpoint — runs the full pipeline for an uploaded recording.

Accepts either an already-uploaded recording (by S3 key, the live path) or an
inline transcript (the offline/demo path, so the prototype is runnable without
AWS). If the numeric-claim validator rejects the generated report, the endpoint
refuses to serve it (502) rather than returning ungrounded feedback.
"""

from __future__ import annotations

from typing import Optional

from botocore.exceptions import ClientError
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, model_validator

from backend.pipeline.report import build_report, report_from_s3


router = APIRouter(prefix="/recordings", tags=["recordings"])


class ReportRequest(BaseModel):
    s3_key: Optional[str] = None
    transcript: Optional[dict] = None

    @model_validator(mode="after")
    def _exactly_one(self) -> "ReportRequest":
        if bool(self.s3_key) == bool(self.transcript):
            raise ValueError("provide exactly one of s3_key or transcript")
        return self


@router.post("/report")
async def create_report(body: ReportRequest) -> dict:
    try:
        if body.s3_key:
            result = report_from_s3(body.s3_key)
        else:
            result = build_report(body.transcript)
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") in {"404", "NoSuchKey"}:
            raise HTTPException(status_code=404, detail=f"No recording found for key: {body.s3_key}")
        raise

    if not result["validation"]["ok"]:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Generated report failed numeric-claim validation and was withheld.",
                "issues": result["validation"]["issues"],
            },
        )
    return result
