"""AI extraction module using OpenAI GPT-4o-mini.

Sends PDF text (or page images for scans) to GPT-4o-mini with Structured Output.
Returns parsed invoice data as a list of dicts.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import RateLimitError, APITimeoutError, APIConnectionError

from src.config import OPENAI_API_KEY, MODEL_PRIMARY, MODEL_FALLBACK, CONFIDENCE_AUTO
from src.modules.pdf_reader import PDFContent

log = logging.getLogger(__name__)

_client = OpenAI(api_key=OPENAI_API_KEY)

# Load system prompt
_PROMPT_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"
_SYSTEM_PROMPT = (_PROMPT_DIR / "v1.txt").read_text(encoding="utf-8")

# JSON schema for Structured Output
_INVOICE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "invoice_extraction",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "invoices": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "invoice_date": {"type": "string", "description": "DD.MM.YYYY"},
                            "truck": {"type": "string", "description": "GR-OO format or empty"},
                            "total_price": {"type": "number", "description": "NETTO, negative for Gutschrift"},
                            "invoice_nr": {"type": "string"},
                            "seller": {"type": "string"},
                            "buyer": {"type": "string"},
                            "kategorie": {
                                "type": "string",
                                "enum": [
                                    "Reparatur", "Ersatzteile", "TÜV/HU/AU", "Reifen",
                                    "Tanken", "Miete", "Wartung", "Versicherung", "Sonstiges",
                                ],
                            },
                            "confidence": {"type": "number", "description": "0.0 to 1.0"},
                        },
                        "required": [
                            "invoice_date", "truck", "total_price", "invoice_nr",
                            "seller", "buyer", "kategorie", "confidence",
                        ],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["invoices"],
            "additionalProperties": False,
        },
    },
}


@dataclass
class ExtractionResult:
    """Result of AI extraction for one PDF."""

    invoices: list[dict[str, Any]] = field(default_factory=list)
    model_used: str = ""
    tokens_input: int = 0
    tokens_output: int = 0
    cost_usd: float = 0.0
    duration_ms: int = 0
    error: str | None = None


# Pricing per 1M tokens (as of 2025)
_PRICING = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
}


def _calc_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    p = _PRICING.get(model, _PRICING["gpt-4o-mini"])
    return (tokens_in * p["input"] + tokens_out * p["output"]) / 1_000_000


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=9),
    retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIConnectionError)),
    before_sleep=lambda rs: log.warning("Retry %d for AI call...", rs.attempt_number),
)
def _call_openai(messages: list[dict], model: str) -> dict:
    """Call OpenAI API with retry logic."""
    return _client.chat.completions.create(
        model=model,
        messages=messages,
        response_format=_INVOICE_SCHEMA,
        temperature=0.0,
        timeout=30,
    )


def extract(pdf_content: PDFContent) -> ExtractionResult:
    """Extract invoice data from PDF content using AI.

    For text PDFs: sends text to GPT-4o-mini.
    For scans: sends images via Vision API.
    If primary model returns low confidence, retries with fallback model.
    """
    start = time.monotonic()

    # Build messages
    if pdf_content.is_scan and pdf_content.page_images_b64:
        messages = _build_vision_messages(pdf_content)
    else:
        messages = _build_text_messages(pdf_content)

    # Try primary model
    result = _try_model(messages, MODEL_PRIMARY, pdf_content.filename)

    # Fallback: if scan with low confidence, try stronger model
    if (
        pdf_content.is_scan
        and result.invoices
        and all(inv.get("confidence", 0) < CONFIDENCE_AUTO for inv in result.invoices)
        and MODEL_FALLBACK != MODEL_PRIMARY
    ):
        log.info("Low confidence from %s for scan %s, trying %s", MODEL_PRIMARY, pdf_content.filename, MODEL_FALLBACK)
        fallback = _try_model(messages, MODEL_FALLBACK, pdf_content.filename)
        if not fallback.error:
            result = fallback

    result.duration_ms = int((time.monotonic() - start) * 1000)
    return result


def _build_text_messages(pdf_content: PDFContent) -> list[dict]:
    return [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": f"Dateiname: {pdf_content.filename}\n\n{pdf_content.text}"},
    ]


def _build_vision_messages(pdf_content: PDFContent) -> list[dict]:
    content_parts: list[dict] = [
        {"type": "text", "text": f"Dateiname: {pdf_content.filename}\n\nBitte extrahiere die Rechnungsdaten aus den folgenden Seitenbildern:"},
    ]
    for b64 in pdf_content.page_images_b64:
        content_parts.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{b64}", "detail": "high"},
        })
    return [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": content_parts},
    ]


def _try_model(messages: list[dict], model: str, filename: str) -> ExtractionResult:
    try:
        resp = _call_openai(messages, model)
        tokens_in = resp.usage.prompt_tokens
        tokens_out = resp.usage.completion_tokens
        cost = _calc_cost(model, tokens_in, tokens_out)

        raw = resp.choices[0].message.content
        data = json.loads(raw)
        invoices = data.get("invoices", [])

        log.info(
            "%s → %s: %d invoices, %d+%d tokens, $%.4f",
            filename, model, len(invoices), tokens_in, tokens_out, cost,
        )

        return ExtractionResult(
            invoices=invoices,
            model_used=model,
            tokens_input=tokens_in,
            tokens_output=tokens_out,
            cost_usd=cost,
        )

    except Exception as e:
        log.error("AI extraction failed for %s with %s: %s", filename, model, e)
        return ExtractionResult(model_used=model, error=str(e))
