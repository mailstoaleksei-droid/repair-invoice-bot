"""Pipeline orchestrator.

Processes a batch of PDFs:
1. Read each PDF (text or scan)
2. Send to AI for extraction
3. Validate extracted data
4. Insert into PostgreSQL
5. Generate Excel
6. Move files (checked / manual)
7. Return summary for Telegram

Supports parallel processing (up to MAX_PARALLEL_PDFS).
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from src.config import (
    CONFIDENCE_AUTO,
    CONFIDENCE_REVIEW,
    DAILY_COST_LIMIT_USD,
    MAX_PARALLEL_PDFS,
    OUTPUT_BASE_FOLDER,
    PDF_FOLDER,
)
from src.modules import ai_extractor, db, excel_writer, file_manager, pdf_reader, validator

log = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Summary of a batch processing run."""

    batch_id: uuid.UUID = field(default_factory=uuid.uuid4)
    total_files: int = 0
    success: int = 0
    review: int = 0
    manual: int = 0
    errors: int = 0
    total_cost: float = 0.0
    excel_path: Path | None = None
    details: list[dict[str, Any]] = field(default_factory=list)
    cost_limit_hit: bool = False


# Type for progress callback: (current, total, detail_line)
ProgressCallback = Callable[[int, int, str], Any] | None


async def process_batch(progress_cb: ProgressCallback = None) -> ProcessingResult:
    """Process all PDFs in the input folder."""
    result = ProcessingResult()

    pdf_files = sorted(PDF_FOLDER.glob("*.pdf"))
    result.total_files = len(pdf_files)

    if not pdf_files:
        return result

    conn = db.get_connection()

    # Check daily cost before starting
    today_cost, _ = db.get_today_cost(conn)
    if today_cost >= DAILY_COST_LIMIT_USD:
        result.cost_limit_hit = True
        conn.close()
        return result

    all_records: list[dict] = []
    sem = asyncio.Semaphore(MAX_PARALLEL_PDFS)

    async def process_one(idx: int, pdf_path: Path) -> None:
        async with sem:
            detail = await asyncio.to_thread(_process_single, conn, result.batch_id, pdf_path, today_cost)
            result.details.append(detail)

            if detail["status"] == "success":
                result.success += 1
                all_records.extend(detail.get("records", []))
            elif detail["status"] == "review":
                result.review += 1
                all_records.extend(detail.get("records", []))
            elif detail["status"] == "manual":
                result.manual += 1
            else:
                result.errors += 1

            result.total_cost += detail.get("cost", 0)

            # Progress callback
            done = result.success + result.review + result.manual + result.errors
            if progress_cb:
                line = _format_detail(detail)
                try:
                    await asyncio.to_thread(progress_cb, done, result.total_files, line)
                except Exception:
                    pass

    tasks = [process_one(i, p) for i, p in enumerate(pdf_files)]
    await asyncio.gather(*tasks)

    # Generate Excel from all successful records
    if all_records:
        output_dir = OUTPUT_BASE_FOLDER / f"RG {all_records[0].get('invoice_year', 2026)} Ersatyteile RepRG"
        result.excel_path = excel_writer.generate(all_records, output_dir)

    conn.close()
    return result


def _process_single(conn, batch_id: uuid.UUID, pdf_path: Path, running_cost: float) -> dict:
    """Process a single PDF file. Runs in a thread."""
    detail: dict[str, Any] = {
        "filename": pdf_path.name,
        "status": "error",
        "records": [],
        "cost": 0,
    }

    try:
        # 1. Read PDF
        content = pdf_reader.read_pdf(pdf_path)
        if content.total_pages == 0:
            detail["status"] = "manual"
            detail["error"] = "Cannot read PDF"
            file_manager.move_to_manual(pdf_path)
            _log_to_db(conn, batch_id, detail)
            return detail

        # 2. AI extraction
        extraction = ai_extractor.extract(content)
        detail["cost"] = extraction.cost_usd
        detail["model"] = extraction.model_used
        detail["tokens_in"] = extraction.tokens_input
        detail["tokens_out"] = extraction.tokens_output

        if extraction.error:
            detail["status"] = "manual"
            detail["error"] = extraction.error
            file_manager.move_to_manual(pdf_path)
            _log_to_db(conn, batch_id, detail)
            return detail

        if not extraction.invoices:
            detail["status"] = "manual"
            detail["error"] = "AI returned no invoices"
            file_manager.move_to_manual(pdf_path)
            _log_to_db(conn, batch_id, detail)
            return detail

        # 3. Validate and enrich each invoice
        valid_records = []
        has_low_confidence = False

        for inv in extraction.invoices:
            is_valid, errors = validator.validate(inv)
            if not is_valid:
                detail["status"] = "manual"
                detail["error"] = f"Validation: {'; '.join(errors)}"
                file_manager.move_to_manual(pdf_path)
                _log_to_db(conn, batch_id, detail)
                return detail

            inv = validator.enrich(inv)
            inv["pdf_filename"] = pdf_path.name
            inv["ai_model"] = extraction.model_used
            inv["prompt_version"] = "v1"
            inv["tokens_used"] = extraction.tokens_input + extraction.tokens_output
            inv["cost_usd"] = extraction.cost_usd / len(extraction.invoices)

            conf = float(inv.get("confidence", 0))
            if conf < CONFIDENCE_REVIEW:
                detail["status"] = "manual"
                detail["error"] = f"Low confidence: {conf:.2f}"
                file_manager.move_to_manual(pdf_path)
                _log_to_db(conn, batch_id, detail)
                return detail

            inv["is_review"] = conf < CONFIDENCE_AUTO
            if inv["is_review"]:
                has_low_confidence = True

            valid_records.append(inv)

        # 4. Insert into DB
        for rec in valid_records:
            inv_id = db.insert_invoice(conn, rec)
            if inv_id is None:
                log.warning("Duplicate: %s / %s / %s", rec["invoice_nr"], rec["seller"], rec["invoice_date"])

        # 5. Move file
        year = valid_records[0].get("invoice_year", 2026)
        file_manager.move_to_checked(pdf_path, year)

        detail["records"] = valid_records
        detail["status"] = "review" if has_low_confidence else "success"

        # 6. Log to DB
        _log_to_db(conn, batch_id, detail, ai_response=extraction.invoices)

    except Exception as e:
        log.exception("Error processing %s", pdf_path.name)
        detail["status"] = "error"
        detail["error"] = str(e)
        try:
            file_manager.move_to_manual(pdf_path)
        except Exception:
            pass
        _log_to_db(conn, batch_id, detail)

    return detail


def _log_to_db(conn, batch_id, detail, ai_response=None):
    """Write processing log entry."""
    try:
        db.log_processing(conn, batch_id, {
            "pdf_filename": detail.get("filename", ""),
            "status": detail["status"],
            "invoice_id": None,
            "error_message": detail.get("error"),
            "ai_model": detail.get("model"),
            "tokens_input": detail.get("tokens_in"),
            "tokens_output": detail.get("tokens_out"),
            "cost_usd": detail.get("cost"),
            "ai_response": ai_response,
            "duration_ms": None,
        })
    except Exception as e:
        log.error("Failed to log processing: %s", e)


def _format_detail(detail: dict) -> str:
    """Format a single result line for Telegram progress."""
    status_icon = {"success": "✓", "review": "⚠", "manual": "✗", "error": "❌"}.get(detail["status"], "?")
    records = detail.get("records", [])
    if records:
        rec = records[0]
        return f"{status_icon} {rec.get('truck', '?')} | {rec.get('seller', '?')[:20]} | {rec.get('total_price', 0):.2f}€ | {rec.get('kategorie', '')}"
    error = detail.get("error", "")[:40]
    return f"{status_icon} {detail['filename'][:30]} | {error}"
