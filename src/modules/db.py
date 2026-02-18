"""PostgreSQL storage module.

Inserts validated invoice records into repair.invoices
and logs processing results in repair.processing_log.
"""

from __future__ import annotations

import logging
import uuid

import psycopg2
import psycopg2.extras

from src.config import DATABASE_URL

log = logging.getLogger(__name__)

_INSERT_INVOICE = """
INSERT INTO repair.invoices
    (invoice_year, invoice_month, invoice_week, invoice_date,
     truck, total_price, invoice_nr, seller, buyer, kategorie,
     pdf_filename, ai_confidence, ai_model, prompt_version,
     tokens_used, cost_usd, is_gutschrift, is_review)
VALUES
    (%(invoice_year)s, %(invoice_month)s, %(invoice_week)s, %(invoice_date_parsed)s,
     %(truck)s, %(total_price)s, %(invoice_nr)s, %(seller)s, %(buyer)s, %(kategorie)s,
     %(pdf_filename)s, %(confidence)s, %(ai_model)s, %(prompt_version)s,
     %(tokens_used)s, %(cost_usd)s, %(is_gutschrift)s, %(is_review)s)
ON CONFLICT (invoice_nr, seller, invoice_date) DO NOTHING
RETURNING id
"""

_INSERT_LOG = """
INSERT INTO repair.processing_log
    (batch_id, pdf_filename, status, invoice_id, error_message,
     ai_model, tokens_input, tokens_output, cost_usd, ai_response, duration_ms)
VALUES
    (%(batch_id)s, %(pdf_filename)s, %(status)s, %(invoice_id)s, %(error_message)s,
     %(ai_model)s, %(tokens_input)s, %(tokens_output)s, %(cost_usd)s,
     %(ai_response)s, %(duration_ms)s)
"""


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def insert_invoice(conn, record: dict) -> int | None:
    """Insert one invoice record. Returns invoice ID or None if duplicate."""
    cur = conn.cursor()
    try:
        cur.execute(_INSERT_INVOICE, record)
        row = cur.fetchone()
        conn.commit()
        return row[0] if row else None
    except Exception as e:
        conn.rollback()
        log.error("DB insert error: %s", e)
        raise
    finally:
        cur.close()


def log_processing(conn, batch_id: uuid.UUID, entry: dict) -> None:
    """Log one processing result."""
    cur = conn.cursor()
    try:
        entry["batch_id"] = str(batch_id)
        if entry.get("ai_response") is not None:
            entry["ai_response"] = psycopg2.extras.Json(entry["ai_response"])
        cur.execute(_INSERT_LOG, entry)
        conn.commit()
    except Exception as e:
        conn.rollback()
        log.error("DB log error: %s", e)
    finally:
        cur.close()


def get_today_cost(conn) -> tuple[float, int]:
    """Return (total_cost_usd, invoice_count) for today."""
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT COALESCE(SUM(cost_usd), 0), COUNT(*)
            FROM repair.processing_log
            WHERE created_at::date = CURRENT_DATE
        """)
        cost, count = cur.fetchone()
        return float(cost), count
    finally:
        cur.close()
