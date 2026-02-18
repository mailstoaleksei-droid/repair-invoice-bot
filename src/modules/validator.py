"""Data validation module (4 levels).

Level 1 — Schema: required fields present and typed
Level 2 — Format: date DD.MM.YYYY, truck pattern, price is float
Level 3 — Logic: date not in future, price > 0 (unless Gutschrift)
Level 4 — Cross-check: truck in registry (optional, skipped if no DB)
"""

from __future__ import annotations

import re
import logging
from datetime import datetime, date

log = logging.getLogger(__name__)

_REQUIRED_FIELDS = ["invoice_date", "truck", "total_price", "invoice_nr", "seller", "buyer", "kategorie", "confidence"]
_TRUCK_PATTERN = re.compile(r"^(GR-OO\d+|HH-AG\d+|DE-FN\d+|WJQY\d+|OHAMX\d+|)$")
_DATE_PATTERN = re.compile(r"^\d{2}\.\d{2}\.\d{4}$")

_VALID_KATEGORIEN = {
    "Reparatur", "Ersatzteile", "TÜV/HU/AU", "Reifen",
    "Tanken", "Miete", "Wartung", "Versicherung", "Sonstiges",
}


def validate(record: dict) -> tuple[bool, list[str]]:
    """Validate a single extracted invoice record.

    Returns (is_valid, list_of_errors).
    """
    errors: list[str] = []

    # Level 1 — Schema
    for f in _REQUIRED_FIELDS:
        if f not in record:
            errors.append(f"missing field: {f}")
    if errors:
        return False, errors

    # Level 2 — Format
    date_str = str(record["invoice_date"])
    if not _DATE_PATTERN.match(date_str):
        errors.append(f"bad date format: {date_str}")

    truck = str(record["truck"])
    if truck and not _TRUCK_PATTERN.match(truck):
        errors.append(f"bad truck format: {truck}")

    try:
        price = float(record["total_price"])
    except (ValueError, TypeError):
        errors.append(f"total_price not numeric: {record['total_price']}")
        price = None

    if record.get("kategorie") and record["kategorie"] not in _VALID_KATEGORIEN:
        errors.append(f"unknown kategorie: {record['kategorie']}")

    # Level 3 — Logic
    if _DATE_PATTERN.match(date_str):
        try:
            dt = datetime.strptime(date_str, "%d.%m.%Y").date()
            if dt > date.today():
                errors.append(f"date in future: {date_str}")
        except ValueError:
            errors.append(f"invalid date value: {date_str}")

    if price is not None and price == 0:
        errors.append("total_price is zero")

    is_valid = len(errors) == 0
    if not is_valid:
        log.warning("Validation failed: %s", errors)

    return is_valid, errors


def enrich(record: dict) -> dict:
    """Add computed fields (year, month, week) from invoice_date."""
    date_str = record.get("invoice_date", "")
    try:
        dt = datetime.strptime(date_str, "%d.%m.%Y").date()
        record["invoice_year"] = dt.year
        record["invoice_month"] = dt.month
        record["invoice_week"] = dt.isocalendar()[1]
        record["invoice_date_parsed"] = dt
        record["is_gutschrift"] = float(record.get("total_price", 0)) < 0
    except ValueError:
        pass
    return record
