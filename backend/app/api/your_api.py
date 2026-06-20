from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter()


class AnalyzeRequest(BaseModel):
    text: str
    model: str | None = "default"


class AnalyzeResponse(BaseModel):
    tenant_id: str
    plan: str
    input_length: int
    result: dict
    latency_ms: float


class SummarizeRequest(BaseModel):
    content: str
    max_length: int | None = 200


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest, request: Request):
    start = time.perf_counter()
    tenant = request.state.tenant

    if req.model == "premium" and tenant.plan == "free":
        raise HTTPException(status_code=403, detail="Premium model requires Pro plan.")

    words = req.text.split()
    request.state.tokens_used = len(words)
    result = {
        "word_count": len(words),
        "char_count": len(req.text),
        "sentences": req.text.count(".") + req.text.count("!") + req.text.count("?"),
        "model_used": req.model,
    }
    latency_ms = (time.perf_counter() - start) * 1000

    return AnalyzeResponse(
        tenant_id=str(tenant.id),
        plan=tenant.plan,
        input_length=len(req.text),
        result=result,
        latency_ms=round(latency_ms, 2),
    )


@router.post("/summarize")
async def summarize(req: SummarizeRequest, request: Request):
    tenant = request.state.tenant
    if tenant.plan == "free":
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Summarization requires Pro plan.",
                "upgrade_url": "/billing",
                "current_plan": "free",
            },
        )

    summary = (
        req.content[: req.max_length] + "..."
        if len(req.content) > req.max_length
        else req.content
    )
    request.state.tokens_used = len(req.content.split())
    return {
        "original_length": len(req.content),
        "summary_length": len(summary),
        "summary": summary,
    }


@router.get("/models")
async def list_models(request: Request):
    tenant = request.state.tenant
    models = {
        "free": [{"id": "default", "description": "Standard model, 100 req/day"}],
        "pro": [
            {"id": "default", "description": "Standard model"},
            {"id": "premium", "description": "Higher accuracy"},
            {"id": "fast", "description": "Lower latency"},
        ],
        "enterprise": [
            {"id": "default", "description": "Standard model"},
            {"id": "premium", "description": "Higher accuracy"},
            {"id": "fast", "description": "Lower latency"},
            {"id": "custom", "description": "Fine-tuned on your data"},
        ],
    }
    return {"plan": tenant.plan, "available_models": models.get(tenant.plan, models["free"])}


@router.get("/health/authed")
async def authed_health(request: Request):
    tenant = request.state.tenant
    return {
        "status": "ok",
        "tenant": tenant.name,
        "plan": tenant.plan,
        "message": "Authentication successful.",
    }
