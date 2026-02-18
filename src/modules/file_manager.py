"""File management module.

Moves processed PDFs to the correct folder:
- Success → RG {YEAR} Ersatzteile RepRG/checked_*.pdf
- Failure → EingangsRG/manual/*.pdf
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from src.config import OUTPUT_BASE_FOLDER, MANUAL_FOLDER

log = logging.getLogger(__name__)


def move_to_checked(pdf_path: Path, year: int) -> Path:
    """Move a successfully processed PDF to the year folder with checked_ prefix."""
    dest_dir = OUTPUT_BASE_FOLDER / f"RG {year} Ersatyteile RepRG"
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest_name = f"checked_{pdf_path.name}"
    dest = dest_dir / dest_name

    # Handle name collision
    counter = 1
    while dest.exists():
        dest = dest_dir / f"checked_{counter}_{pdf_path.name}"
        counter += 1

    shutil.move(str(pdf_path), str(dest))
    log.info("Moved to checked: %s → %s", pdf_path.name, dest)
    return dest


def move_to_manual(pdf_path: Path) -> Path:
    """Move a failed PDF to the manual/ folder."""
    dest_dir = Path(MANUAL_FOLDER)
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest = dest_dir / pdf_path.name

    # Handle name collision
    counter = 1
    while dest.exists():
        dest = dest_dir / f"{counter}_{pdf_path.name}"
        counter += 1

    shutil.move(str(pdf_path), str(dest))
    log.info("Moved to manual: %s → %s", pdf_path.name, dest)
    return dest


def list_manual_files() -> list[Path]:
    """List PDF files in the manual/ folder."""
    dest_dir = Path(MANUAL_FOLDER)
    if not dest_dir.exists():
        return []
    return sorted(dest_dir.glob("*.pdf"))
