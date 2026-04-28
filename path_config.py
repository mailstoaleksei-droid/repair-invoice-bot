import os
import re
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


PROJECT_DIR = Path(__file__).resolve().parent
if load_dotenv:
    load_dotenv(PROJECT_DIR / ".env")

DEFAULT_DATA_ROOT = Path(
    r"C:\Users\Aleksei Samosvat\Groo GmbH\Intranet - Groo GmbH - Dokumente\Auto Compass GmbH\AC - Fahrzeuge\Ablage\Eingangs Rechnungen"
)


def _year_from_name(path: Path) -> int:
    match = re.search(r"RG\s+(\d{4})", path.name)
    return int(match.group(1)) if match else 0


def get_data_root() -> Path:
    override = os.getenv("REPAIR_DATA_ROOT", "").strip()
    if override:
        return Path(override)
    return DEFAULT_DATA_ROOT


def list_rg_folders(data_root: Path) -> list[Path]:
    folders = []
    if data_root.exists():
        for child in data_root.iterdir():
            if child.is_dir() and child.name.startswith("RG "):
                folders.append(child)
    return sorted(folders, key=_year_from_name, reverse=True)


def find_year_folder(data_root: Path, year: int) -> Path:
    year_str = str(year)
    for folder in list_rg_folders(data_root):
        if year_str in folder.name:
            return folder
    return data_root / f"RG {year_str} Ersatyteile RepRG"


def find_master_excel(data_root: Path) -> Path:
    repair_candidates = []
    batch_candidates = []

    for folder in list_rg_folders(data_root):
        for candidate in folder.glob("*.xlsx"):
            lower_name = candidate.name.lower()
            if lower_name.startswith("repair_"):
                repair_candidates.append(candidate)
            elif lower_name.startswith("rechnungen_"):
                batch_candidates.append(candidate)

    if repair_candidates:
        return max(repair_candidates, key=lambda item: item.stat().st_mtime)
    if batch_candidates:
        return max(batch_candidates, key=lambda item: item.stat().st_mtime)

    current_year = datetime.now().year
    return find_year_folder(data_root, current_year) / f"Repair_{current_year}.xlsx"


DATA_ROOT = get_data_root()
PDF_FOLDER = DATA_ROOT / "EingangsRG"
MANUAL_FOLDER = PDF_FOLDER / "manual"
CURRENT_YEAR_FOLDER = find_year_folder(DATA_ROOT, datetime.now().year)
EXCEL_FILE = find_master_excel(DATA_ROOT)
PROCESSED_FOLDER = CURRENT_YEAR_FOLDER
LOG_FOLDER = PROJECT_DIR / "logs"
REPORT_FOLDER = PROJECT_DIR / "reports"
