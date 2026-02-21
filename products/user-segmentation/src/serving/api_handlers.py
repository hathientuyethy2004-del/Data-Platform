from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict

from fastapi import FastAPI
from pydantic import BaseModel, Field


class SegmentRequest(BaseModel):
    user_id: str
    recency_days: int = Field(..., ge=0)
    frequency: int = Field(..., ge=0)
    monetary: float = Field(..., ge=0)


class SegmentResponse(BaseModel):
    user_id: str
    segment: str
    confidence: float


def classify_segment(payload: SegmentRequest) -> SegmentResponse:
    if payload.monetary >= 1000 and payload.frequency >= 5 and payload.recency_days <= 30:
        segment = "VIP"
        confidence = 0.92
    elif payload.frequency >= 3 and payload.recency_days <= 60:
        segment = "Active"
        confidence = 0.84
    elif payload.recency_days >= 120:
        segment = "Dormant"
        confidence = 0.88
    else:
        segment = "At_Risk"
        confidence = 0.76

    return SegmentResponse(user_id=payload.user_id, segment=segment, confidence=confidence)


app = FastAPI(title="User Segmentation API", version="0.1.0")


@app.get("/health")
def health() -> Dict[str, str]:
    return {
        "status": "healthy",
        "product": "user-segmentation",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/segments/classify", response_model=SegmentResponse)
def classify(payload: SegmentRequest) -> SegmentResponse:
    return classify_segment(payload)
