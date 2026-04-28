import base64
import json
import os
import re
from datetime import datetime

import fitz
from dotenv import load_dotenv
from openai import OpenAI

from supplier_reference import extract_company_name_only
from truck_reference import normalize_truck_candidate, extract_normalized_truck_number, strip_truck_number_from_text

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(PROJECT_DIR, ".env"))


def _env_flag(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def is_ai_available():
    return _env_flag("OPENAI_ENABLED", False) and bool(os.getenv("OPENAI_API_KEY"))


def _build_client():
    return OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        timeout=float(os.getenv("OPENAI_TIMEOUT", "90")),
    )


def _normalize_date(date_str):
    if not date_str:
        return "", None

    candidates = [
        ("%d/%m/%Y", "%d.%m.%Y"),
        ("%d.%m.%Y", "%d.%m.%Y"),
        ("%Y-%m-%d", "%d.%m.%Y"),
    ]

    for source_fmt, target_fmt in candidates:
        try:
            date_obj = datetime.strptime(str(date_str).strip(), source_fmt)
            return date_obj.strftime(target_fmt), date_obj
        except ValueError:
            continue

    return str(date_str).strip(), None


def _render_pdf_images(pdf_path, max_pages=3):
    image_items = []
    doc = fitz.open(pdf_path)
    try:
        page_count = min(len(doc), max_pages)
        for page_index in range(page_count):
            page = doc.load_page(page_index)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            encoded = base64.b64encode(pix.tobytes("png")).decode("ascii")
            image_items.append({
                "type": "input_image",
                "image_url": f"data:image/png;base64,{encoded}",
            })
    finally:
        doc.close()

    return image_items


def _build_schema():
    return {
        "type": "object",
        "properties": {
            "invoice_number": {"type": "string"},
            "invoice_date": {"type": "string"},
            "seller": {"type": "string"},
            "buyer": {"type": "string"},
            "is_internal_invoice": {"type": "boolean"},
            "currency": {"type": "string"},
            "document_total_net": {"type": "number"},
            "vehicles": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "truck": {"type": "string"},
                        "name": {"type": "string"},
                        "category": {"type": "string"},
                        "total_price_net": {"type": "number"},
                    },
                    "required": ["truck", "name", "category", "total_price_net"],
                    "additionalProperties": False,
                },
            },
            "document_level_notes": {"type": "string"},
            "missing_fields": {
                "type": "array",
                "items": {"type": "string"},
            },
            "confidence": {"type": "number"},
        },
        "required": [
            "invoice_number",
            "invoice_date",
            "seller",
            "buyer",
            "is_internal_invoice",
            "currency",
            "document_total_net",
            "vehicles",
            "document_level_notes",
            "missing_fields",
            "confidence",
        ],
        "additionalProperties": False,
    }


def _build_prompt(filename, supplier_hint="", text_content="", partial_data=None):
    partial_data = partial_data or {}
    prompt = [
        "Extract invoice data for truck repair accounting.",
        "Return only valid JSON matching the schema.",
        "Use net amounts only.",
        "If seller equals buyer, treat it as an internal invoice and do not recalculate net.",
        "If multiple trucks are present, return one vehicle item per truck.",
        "If there is only one truck and a single net total in the document, assign that net total to that truck.",
        "Truck numbers must be returned only in the truck field, never in the name field.",
        "Use German or English invoice understanding as needed.",
        f"Filename: {filename}",
    ]
    if supplier_hint:
        prompt.append(f"Supplier hint from Python parser: {supplier_hint}")
    if partial_data:
        prompt.append("Partial data already extracted by Python:")
        prompt.append(json.dumps(partial_data, ensure_ascii=False))
    if text_content.strip():
        prompt.append("Invoice text extracted by Python:")
        prompt.append(text_content[:30000])
    else:
        prompt.append("Python could not extract usable text. Use the images.")
    return "\n".join(prompt)


def _normalize_ai_payload(payload, supplier_hint=""):
    invoice_date, date_obj = _normalize_date(payload.get("invoice_date", ""))
    seller = payload.get("seller", "").strip() or supplier_hint
    buyer = payload.get("buyer", "").strip()
    document_total = float(payload.get("document_total_net", 0) or 0)
    vehicles = payload.get("vehicles") or []

    line_items = []
    for vehicle in vehicles:
        total_price = float(vehicle.get("total_price_net", 0) or 0)
        truck_value = normalize_truck_candidate(vehicle.get("truck", ""))
        name_value = vehicle.get("name", "").strip()
        if not truck_value:
            truck_value = extract_normalized_truck_number(name_value)
        if truck_value:
            name_value = strip_truck_number_from_text(name_value)
            name_value = re.sub(
                r"(?i)\b(?:kennzeichen|amtl\.?\s*kennz\.?|amtl|truck|fahrzeug|fahrgestell(?:-?nr)?|vin|fz)\b",
                " ",
                name_value,
            )
            name_value = re.sub(r"[()\[\]{}:;/,_-]+", " ", name_value)
            name_value = re.sub(r"\s+", " ", name_value).strip()
            if not re.search(r"[A-Za-zÄÖÜäöüА-Яа-я]", name_value):
                name_value = ""

        line_items.append({
            "truck": truck_value,
            "name": name_value,
            "category": vehicle.get("category", "").strip(),
            "total_price": total_price,
        })

    if not line_items and document_total > 0:
        line_items.append({
            "truck": "",
            "name": "",
            "category": "",
            "total_price": document_total,
        })

    first_item = line_items[0] if line_items else {}
    normalized = {
        "invoice": payload.get("invoice_number", "").strip(),
        "date": invoice_date,
        "seller": seller,
        "buyer": buyer,
        "truck": first_item.get("truck", ""),
        "name": first_item.get("name", ""),
        "category": first_item.get("category", ""),
        "total_price": first_item.get("total_price", document_total),
        "line_items": line_items,
        "extraction_source": "ai",
        "ai_confidence": float(payload.get("confidence", 0) or 0),
        "ai_missing_fields": payload.get("missing_fields", []),
        "ai_notes": payload.get("document_level_notes", ""),
        "supplier_hint": supplier_hint,
    }

    if date_obj:
        normalized["year"] = date_obj.year
        normalized["month"] = date_obj.month
        normalized["week"] = date_obj.isocalendar()[1]

    if normalized["seller"]:
        normalized["seller"] = extract_company_name_only(normalized["seller"])
    if normalized["buyer"]:
        normalized["buyer"] = extract_company_name_only(normalized["buyer"])

    return normalized


def extract_invoice_with_ai(pdf_path, filename, supplier_hint="", text_content="", partial_data=None):
    if not is_ai_available():
        return None, "ai_not_configured"

    try:
        client = _build_client()
        max_pages = int(os.getenv("OPENAI_MAX_PAGES", "3"))
        prompt = _build_prompt(
            filename=filename,
            supplier_hint=supplier_hint,
            text_content=text_content,
            partial_data=partial_data,
        )

        user_content = [{"type": "input_text", "text": prompt}]
        user_content.extend(_render_pdf_images(pdf_path, max_pages=max_pages))

        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-5-mini"),
            input=[
                {
                    "role": "system",
                    "content": [{
                        "type": "input_text",
                        "text": (
                            "You extract structured invoice data for truck maintenance accounting. "
                            "Return only JSON. Use net amounts only. "
                            "Be conservative and list missing fields if uncertain."
                        ),
                    }],
                },
                {
                    "role": "user",
                    "content": user_content,
                },
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "invoice_extract",
                    "strict": True,
                    "schema": _build_schema(),
                }
            },
        )

        payload = json.loads(response.output_text)
        normalized = _normalize_ai_payload(payload, supplier_hint=supplier_hint)
        if not normalized.get("invoice") or not normalized.get("date"):
            return None, "ai_incomplete"
        return normalized, None
    except Exception as exc:
        return None, f"ai_error:{str(exc)[:200]}"
