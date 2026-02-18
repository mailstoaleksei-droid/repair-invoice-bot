"""PDF text extraction module.

Extracts text from PDF files using pdfplumber.
Detects scanned PDFs (little/no text) and converts pages to images
for Vision API processing.
"""

from __future__ import annotations

import base64
import logging
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path

import pdfplumber

log = logging.getLogger(__name__)

# If a page yields fewer characters than this, treat it as a scan.
_SCAN_TEXT_THRESHOLD = 50


@dataclass
class PDFContent:
    """Result of reading a single PDF file."""

    filename: str
    total_pages: int
    text: str  # concatenated text from all pages (may be empty for scans)
    is_scan: bool  # True if most pages have very little text
    page_images_b64: list[str] = field(default_factory=list)  # base64 PNG per page (only for scans)


def read_pdf(path: Path) -> PDFContent:
    """Read a PDF and return its content.

    For text-based PDFs: returns extracted text.
    For scanned PDFs: returns base64-encoded page images for Vision API.
    """
    filename = path.name
    all_text_parts: list[str] = []
    scan_pages = 0
    total_pages = 0

    try:
        with pdfplumber.open(path) as pdf:
            total_pages = len(pdf.pages)
            for page in pdf.pages:
                try:
                    page_text = page.extract_text() or ""
                except Exception as e:
                    log.warning("Page %d text extraction failed in %s: %s", page.page_number, filename, e)
                    page_text = ""

                all_text_parts.append(page_text)
                if len(page_text.strip()) < _SCAN_TEXT_THRESHOLD:
                    scan_pages += 1
    except Exception as e:
        log.error("Failed to open PDF %s: %s", filename, e)
        return PDFContent(
            filename=filename,
            total_pages=0,
            text="",
            is_scan=True,
        )

    full_text = "\n\n".join(all_text_parts)
    is_scan = total_pages > 0 and scan_pages > total_pages / 2

    result = PDFContent(
        filename=filename,
        total_pages=total_pages,
        text=full_text,
        is_scan=is_scan,
    )

    if is_scan:
        log.info("%s detected as SCAN (%d/%d pages with <50 chars)", filename, scan_pages, total_pages)
        result.page_images_b64 = _convert_to_images(path)
    else:
        log.info("%s is TEXT-based (%d pages, %d chars)", filename, total_pages, len(full_text))

    return result


def _convert_to_images(path: Path) -> list[str]:
    """Convert PDF pages to base64-encoded PNG images for Vision API."""
    try:
        from pdf2image import convert_from_path

        images = convert_from_path(
            str(path),
            dpi=200,
            fmt="png",
        )
        result = []
        for img in images:
            buf = BytesIO()
            img.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            result.append(b64)
        return result

    except ImportError:
        log.error("pdf2image not installed — cannot convert scanned PDF to images")
        return []
    except Exception as e:
        log.error("Failed to convert %s to images: %s", path.name, e)
        return []
