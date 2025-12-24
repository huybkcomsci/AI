#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import json
import time
import os
from typing import Any, Dict, List

import requests
from fastapi import APIRouter, FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from config import Config


# -----------------------------
# Tunables (env override)
# -----------------------------
MAX_PDF_PAGES = int(os.getenv("MAX_PDF_PAGES", "5"))          # chỉ lấy tối đa N trang
MAX_PDF_TEXT_CHARS = int(os.getenv("MAX_PDF_TEXT_CHARS", "35000"))  # cắt text trước khi gửi LLM
CONNECT_TIMEOUT = float(os.getenv("CONNECT_TIMEOUT", "10"))
READ_TIMEOUT = float(os.getenv("READ_TIMEOUT", "120"))       # DeepSeek thường lâu -> tăng
MIN_CONFIDENCE_TO_RECORD = float(os.getenv("MIN_CONFIDENCE_TO_RECORD", "0.75"))


# -----------------------------
# Core helpers
# -----------------------------
def log(msg: str) -> None:
    print(f"[serverAI] {msg}", flush=True)


def build_A(api_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    data = api_json.get("data", [])
    return [{"metric_id": m.get("metric_id"), "name": m.get("name"), "unit": m.get("unit")} for m in data]


def _normalize_text(s: str) -> str:
    # nhẹ nhàng: loại bớt khoảng trắng thừa (giảm token)
    s = s.replace("\r", "\n")
    while "\n\n\n" in s:
        s = s.replace("\n\n\n", "\n\n")
    return s.strip()


def pdf_bytes_to_text(pdf_bytes: bytes) -> str:
    """
    Extract text from PDF bytes, page-limited, memory-safe:
    - Try PyPDF2 first (lighter)
    - Fallback pdfplumber if needed
    """
    # 1) Try PyPDF2 first
    try:
        from PyPDF2 import PdfReader  # type: ignore

        reader = PdfReader(io.BytesIO(pdf_bytes))
        chunks: List[str] = []
        pages = reader.pages[:MAX_PDF_PAGES]
        for page in pages:
            text = page.extract_text() or ""
            if text.strip():
                chunks.append(text)

        out = "\n\n".join(chunks).strip()
        if out:
            return out
    except Exception:
        pass

    # 2) Fallback: pdfplumber (nặng hơn)
    try:
        import pdfplumber  # type: ignore

        chunks = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for i, page in enumerate(pdf.pages[:MAX_PDF_PAGES]):
                text = page.extract_text() or ""
                if text.strip():
                    chunks.append(text)

        out = "\n\n".join(chunks).strip()
        return out
    except Exception as exc:
        raise RuntimeError("Cannot extract text from PDF (maybe scanned image). OCR needed.") from exc


def deepseek_one_shot(A: List[Dict[str, Any]], pdf_text: str) -> Dict[str, Any]:
    """
    Call DeepSeek via HTTP. Output includes records_template ready for origin API.
    """
    api_key = getattr(Config, "DEEPSEEK_API_KEY", None) or None
    base_url = getattr(Config, "DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
    model = getattr(Config, "MODEL", "deepseek-chat")

    if not api_key:
        raise RuntimeError("Missing DEEPSEEK_API_KEY env var.")

    prompt_payload = {
        "task": (
            "Extract lab test results from PDF text, match them to API metrics list A, "
            "and prepare record templates for posting to the origin system"
        ),
        "A": A,
        "pdf_text": pdf_text,
        "unit_conversion_hints": [
            "Glucose: 1 mmol/L = 18 mg/dL",
            "Creatinine: 1 mg/dL = 88.4 µmol/L",
            "Cholesterol/LDL/HDL: 1 mmol/L = 38.67 mg/dL",
            "Triglycerides: 1 mmol/L = 88.57 mg/dL",
        ],
        "rules": [
            "metric_id differs per patient; match by meaning/semantics, not by id.",
            "Extract lab_items first (test_name/value/unit, alt_values if both units appear).",
            "Then produce matches for each item in A.",
            f"Create records_template ONLY for matches with matched=true and confidence>={MIN_CONFIDENCE_TO_RECORD}.",
            "records_template must be sufficient for client to call: POST /api/health-metrics/{patientId}/{metricId}/values (client provides patientId).",
            "Set record.body.value to normalized_value_in_api_unit if available; else use raw file_value only if file_unit matches api_unit (or api_unit is null).",
            "Set record.body.time ONLY if explicitly present in the PDF; otherwise set null (do NOT guess).",
            "Return STRICT JSON only (no markdown).",
        ],
        "output_schema": {
            "lab_items": [
                {
                    "test_name": "string",
                    "value": "number|string|boolean|object",
                    "unit": "string|null",
                    "time": "string|null",
                    "alt_values": [{"value": "number|string|boolean|object", "unit": "string"}],
                    "source_hint": "string",
                }
            ],
            "matches": [
                {
                    "metric_id": "number",
                    "metric_name": "string",
                    "api_unit": "string|null",
                    "matched": "boolean",
                    "file_test_name": "string|null",
                    "file_value": "number|string|boolean|object|null",
                    "file_unit": "string|null",
                    "normalized_value_in_api_unit": "number|string|boolean|object|null",
                    "normalized_unit": "string|null",
                    "confidence": "number",
                    "note": "string",
                    "candidates": [{"test_name": "string", "confidence": "number", "note": "string"}],
                }
            ],
            "records_template": [
                {
                    "metricId": "number",
                    "body": {"value": "number|string|boolean|object", "time": "string|null"},
                    "confidence": "number",
                    "derived_from": {
                        "metric_id": "number",
                        "metric_name": "string",
                        "file_test_name": "string",
                    },
                    "warnings": ["string"],
                }
            ],
        },
    }

    body = {
        "model": model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a medical report parser and matcher.\n"
                    "Return STRICT JSON only, matching the requested schema.\n"
                    "Do not hallucinate values not present in the report."
                ),
            },
            {"role": "user", "content": json.dumps(prompt_payload, ensure_ascii=False)},
        ],
    }

    url = f"{base_url}/chat/completions"
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=body,
        timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
    )
    resp.raise_for_status()
    data = resp.json()

    content = (data.get("choices", [{}])[0].get("message", {}) or {}).get("content", "") or ""
    content = content.strip()
    if not content:
        raise RuntimeError("DeepSeek returned empty content.")
    return json.loads(content)


router = APIRouter(tags=["serverAI"])


@router.get("/")
def root():
    return {"ok": True}


@router.get("/health")
def health():
    return {"ok": True}


@router.post("/match")
async def match_metrics(
    metrics_json: str = Form(..., description="Raw JSON string from GET /api/health-metrics/{patientId}"),
    pdf: UploadFile = File(..., description="PDF lab report"),
):
    t0 = time.time()

    # Parse metrics JSON
    try:
        api_json = json.loads(metrics_json)
    except Exception:
        raise HTTPException(status_code=400, detail="metrics_json is not valid JSON string.")

    A = build_A(api_json)
    if not A:
        raise HTTPException(status_code=400, detail="Cannot extract metrics A: missing data[] or empty data.")

    # Read PDF bytes
    if pdf.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail=f"Invalid content_type for pdf: {pdf.content_type}")

    pdf_bytes = await pdf.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Empty PDF file.")

    log(f"Received metrics_json length={len(metrics_json)}, metrics_count={len(A)}, pdf_size={len(pdf_bytes)} bytes")

    # Extract text (limited)
    t1 = time.time()
    try:
        pdf_text = pdf_bytes_to_text(pdf_bytes)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF text extraction failed: {exc}")

    pdf_text = _normalize_text(pdf_text)

    if not pdf_text.strip():
        raise HTTPException(status_code=422, detail="Extracted PDF text is empty. PDF may be scanned image; OCR is needed.")

    # Truncate to reduce token/memory + speed up LLM
    if len(pdf_text) > MAX_PDF_TEXT_CHARS:
        pdf_text = pdf_text[:MAX_PDF_TEXT_CHARS] + "\n\n[TRUNCATED]"
    log(f"PDF extract done in {time.time()-t1:.2f}s, pdf_text_chars={len(pdf_text)}")

    # Call DeepSeek
    t2 = time.time()
    try:
        result = deepseek_one_shot(A, pdf_text)
    except Exception as exc:
        log(f"DeepSeek error: {exc}")
        raise HTTPException(status_code=500, detail=f"DeepSeek call failed: {exc}")
    log(f"DeepSeek done in {time.time()-t2:.2f}s")

    matches = result.get("matches", []) or []
    records_template = result.get("records_template", []) or []

    # Trả về cho client: đủ để client tự POST lại API gốc (client tự nhập patientId)
    out = {
        "success": True,
        "data": {
            "matches": matches,
            "records_template": records_template,
            "posting_guide": {
                "origin_endpoint": "/api/health-metrics/{patientId}/{metricId}/values",
                "example": {
                    "path": "/api/health-metrics/{patientId}/{metricId}/values",
                    "body": {"value": 95, "time": "2024-01-15T08:00:00.000Z"},
                },
                "note": "Client must provide patientId when posting to origin system. Use metricId from records_template.metricId and body as-is.",
            },
        },
        "meta": {
            "max_pdf_pages": MAX_PDF_PAGES,
            "max_pdf_text_chars": MAX_PDF_TEXT_CHARS,
            "elapsed_sec": round(time.time() - t0, 3),
        },
    }

    return JSONResponse(out)


def create_server_ai_app() -> FastAPI:
    app = FastAPI(
        title="serverAI",
        description="Parse PDF + match to patient-specific metrics, returning payload templates to POST back to origin system.",
        version="1.0.1",
    )
    app.include_router(router)
    return app


app = create_server_ai_app()

__all__ = ["app", "router", "create_server_ai_app"]
