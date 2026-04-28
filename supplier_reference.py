import re


SUPPLIER_REFERENCE_HINTS = {
    "Auto Compass (Internal)": [
        "AUTO COMPASS",
        "AUTO COMPASS GMBH",
    ],
    "Vital Projekt": [
        "VITAL PROJEKT",
    ],
    "DEKRA": [
        "DEKRA",
        "DEKRA AUTOMOBIL",
    ],
    "Scania External": [
        "SCANIA",
    ],
    "Ferronordic": [
        "FERRONORDIC",
    ],
    "HNS": [
        "HNS",
        "HNS NUTZFAHRZEUGE",
        "HNS SERVICE",
    ],
    "TIP": [
        "TIP TRAILER",
        "TRAILER SERVICES GERMANY",
    ],
    "Euromaster": [
        "EUROMASTER",
    ],
    "MAN": [
        "MAN TRUCK",
        "MAN TRUCK & BUS",
    ],
    "Schütt": [
        "SCHUTT",
        "SCHUETT",
        "SCHÜTT",
        "W. SCHUTT",
        "W. SCHUETT",
        "W. SCHÜTT",
    ],
    "Volvo": [
        "VOLVO",
        "VOLVO GROUP TRUCKS",
    ],
    "Sotecs": [
        "SOTECS",
    ],
    "Express": [
        "EXPRESS",
        "EXPRESS SERVICE",
    ],
    "K&L": [
        "K&L",
        "KFZ MEISTERBETRIEB",
    ],
    "Quick": [
        "QUICK REIFEN",
        "REIFENDISCOUNT",
    ],
    "Tankpool24": [
        "TANKPOOL",
    ],
    "Winkler": [
        "WINKLER",
    ],
    "LKWASH": [
        "LKWASH",
    ],
    "Diesel Technic": [
        "DIESEL TECHNIC",
    ],
    "Mobis": [
        "MOBIS",
    ],
    "Hettich": [
        "HETTICH",
    ],
    "Bauer": [
        "BAUER",
    ],
    "YellowFox": [
        "YELLOWFOX",
    ],
    "AFK Bank": [
        "AFK BANK",
    ],
}


def normalize_supplier_text(value):
    """Normalize supplier text for robust keyword matching."""
    text = str(value or "").upper()
    replacements = {
        "Ä": "AE",
        "Ö": "OE",
        "Ü": "UE",
        "ß": "SS",
        "&AMP;": "&",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


LEGAL_FORM_PATTERNS = [
    r"GMBH\s*&\s*CO\.\s*KG",
    r"GMBH\s+CO\.\s*KG",
    r"GMBH",
    r"UG\s*\(HAFTUNGSBESCHR[ÄA]NKT\)",
    r"UG",
    r"AG",
    r"KG",
    r"OHG",
    r"GBR",
    r"SE",
    r"EK",
    r"E\.K\.",
    r"LLC",
    r"LTD",
    r"INC",
    r"BV",
    r"SRL",
    r"SAS",
]


def _canonicalize_legal_forms(company_name):
    replacements = {
        r"\bGMBH\s*&\s*CO\.\s*KG\b": "GmbH & Co. KG",
        r"\bGMBH\s+CO\.\s*KG\b": "GmbH Co. KG",
        r"\bGMBH\b": "GmbH",
        r"\bUG\s*\(HAFTUNGSBESCHR[ÄA]NKT\)\b": "UG (haftungsbeschränkt)",
        r"\bUG\b": "UG",
        r"\bAG\b": "AG",
        r"\bKG\b": "KG",
        r"\bOHG\b": "OHG",
        r"\bGBR\b": "GbR",
        r"\bSE\b": "SE",
        r"\bEK\b": "eK",
        r"\bE\.K\.\b": "e.K.",
        r"\bLLC\b": "LLC",
        r"\bLTD\b": "Ltd",
        r"\bINC\b": "Inc",
        r"\bBV\b": "BV",
        r"\bSRL\b": "SRL",
        r"\bSAS\b": "SAS",
    }

    cleaned = company_name
    for pattern, replacement in replacements.items():
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
    return cleaned


def extract_company_name_only(value):
    """
    Extract only the company name from seller/buyer text.
    Example:
    "Auto Compass Gmbh, Randersweide 1, 21035 Hamburg" -> "Auto Compass GmbH"
    """
    text = str(value or "").strip()
    if not text:
        return ""

    text = re.sub(r"[\r\n]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" ,;:-")
    text = re.sub(
        r"^(?:firma|buyer|seller|lieferant|kunde|rechnungsempf[aä]nger)\s*[:\-]?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    legal_form_pattern = "|".join(LEGAL_FORM_PATTERNS)
    company_match = re.search(
        rf"^\s*(.+?\b(?:{legal_form_pattern})\b)",
        text,
        flags=re.IGNORECASE,
    )
    if company_match:
        company_name = company_match.group(1).strip(" ,;:-")
        return _canonicalize_legal_forms(company_name)

    comma_split = re.split(r"\s*,\s*", text, maxsplit=1)
    if comma_split:
        return comma_split[0].strip()

    return text


def extract_reference_suppliers(text):
    """Return normalized supplier matches based on the reference hint list."""
    haystack = normalize_supplier_text(text)
    matches = []

    for supplier_name, keywords in SUPPLIER_REFERENCE_HINTS.items():
        for keyword in keywords:
            normalized_keyword = normalize_supplier_text(keyword)
            if normalized_keyword and normalized_keyword in haystack:
                matches.append(supplier_name)
                break

    return matches
