#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI "serverAI" (stateless):
- Client gửi: metrics JSON (GET /api/health-metrics/{patientId} response) + file PDF
- ServerAI trả về:
  - matches[]
  - records_template[]  (đủ để client POST lại hệ thống gốc)
    => mỗi record có metricId, body {value, time}, confidence, warning...
- Client tự gắn patientId khi gọi API gốc:
    POST /api/health-metrics/{patientId}/{metricId}/values

Run:
  export DEEPSEEK_API_KEY="sk-..."
  uvicorn server_ai:app --host 0.0.0.0 --port 8000 --reload

Test:
  curl -X POST "http://localhost:8000/match" \
    -F 'metrics_json={"success":true,"data":[{"metric_id":6,"name":"HbA1c","unit":"%"}]}' \
    -F 'pdf=@DIAG.pdf;type=application/pdf'
"""

import io
import json
from typing import Any, Dict, List

from fastapi import APIRouter, FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from config import Config


# -----------------------------
# Core helpers
# -----------------------------
def build_A(api_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    data = api_json.get("data", [])
    return [
        {"metric_id": m.get("metric_id"), "name": m.get("name"), "unit": m.get("unit")}
        for m in data
    ]


def pdf_bytes_to_text(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes; prefer pdfplumber for layout preservation."""
    try:
        import pdfplumber  # type: ignore

        chunks: List[str] = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                if text.strip():
                    chunks.append(text)
        output = "\n\n".join(chunks).strip()
        if output:
            return output
    except Exception:
        pass

    try:
        from PyPDF2 import PdfReader  # type: ignore

        reader = PdfReader(io.BytesIO(pdf_bytes))
        chunks: List[str] = []
        for page in reader.pages:
            text = page.extract_text() or ""
            if text.strip():
                chunks.append(text)
        return "\n\n".join(chunks).strip()
    except Exception as exc:
        raise RuntimeError(
            "Cannot extract text from PDF. The PDF may be scanned image; OCR is needed."
        ) from exc


def deepseek_one_shot(A: List[Dict[str, Any]], pdf_text: str) -> Dict[str, Any]:
    api_key = Config.DEEPSEEK_API_KEY or None
    base_url = Config.DEEPSEEK_BASE_URL.rstrip("/") if hasattr(Config, "DEEPSEEK_BASE_URL") else ""
    model = getattr(Config, "MODEL", "deepseek-chat")
    if not api_key:
        raise RuntimeError("Missing DEEPSEEK_API_KEY env var.")

    try:
        from openai import OpenAI  # type: ignore
    except Exception as exc:  # pragma: no cover - import error is runtime env issue
        raise RuntimeError("openai package is required for DeepSeek call.") from exc

    client = OpenAI(api_key=api_key, base_url=base_url or "https://api.deepseek.com")

    payload = {
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
            "Create records_template ONLY for matches with matched=true and confidence>=0.75.",
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

    resp = client.chat.completions.create(
        model=model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a medical report parser and matcher.\n"
                    "Return STRICT JSON only, matching the requested schema.\n"
                    "Do not hallucinate values not present in the report."
                ),
            },
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
    )

    content = (resp.choices[0].message.content or "").strip()
    if not content:
        raise RuntimeError("DeepSeek returned empty content.")
    return json.loads(content)


router = APIRouter(tags=["serverAI"])


@router.get("/health")
def health():
    return {"ok": True}


@router.post("/match")
async def match_metrics(
    metrics_json: str = Form(..., description="Raw JSON string from GET /api/health-metrics/{patientId}"),
    pdf: UploadFile = File(..., description="PDF lab report"),
):
    try:
        api_json = json.loads(metrics_json)
    except Exception:
        raise HTTPException(status_code=400, detail="metrics_json is not valid JSON string.")

    A = build_A(api_json)
    if not A:
        raise HTTPException(status_code=400, detail="Cannot extract metrics A: missing data[] or empty data.")

    if pdf.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail=f"Invalid content_type for pdf: {pdf.content_type}")

    pdf_bytes = await pdf.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Empty PDF file.")

    try:
        pdf_text = pdf_bytes_to_text(pdf_bytes)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF text extraction failed: {exc}")

    if not pdf_text.strip():
        raise HTTPException(
            status_code=422,
            detail="Extracted PDF text is empty. PDF may be scanned image; OCR is needed.",
        )

    try:
        result = deepseek_one_shot(A, pdf_text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"DeepSeek call failed: {exc}")

    matches = result.get("matches", []) or []
    records_template = result.get("records_template", []) or []
    lab_items = result.get("lab_items", []) or []

    return JSONResponse(
        {
            "success": True,
            "data": {
                "matches": matches,
                "records_template": records_template,
                "lab_items": lab_items,
                "posting_guide": {
                    "origin_endpoint": "/api/health-metrics/{patientId}/{metricId}/values",
                    "note": "Client must provide patientId when posting to origin system. Use metricId from records_template.metricId and body as-is.",
                },
            },
        }
    )


def create_server_ai_app() -> FastAPI:
    app = FastAPI(
        title="serverAI",
        description=(
            "Parse PDF + match to patient-specific metrics, returning payload templates to POST back to origin system."
        ),
        version="1.0.0",
    )
    app.include_router(router)
    return app


app = create_server_ai_app()


__all__ = ["app", "router", "create_server_ai_app"]
