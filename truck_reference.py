import re

# Incomplete truck reference derived from the user's screenshot and current project data.
# This file is used as a hint source for normalization and fallback matching.

TRUCK_PREFIX_PATTERNS = [
    r"\bGR[-\s]?OO[-\s]*\d{2,4}\b",
    r"\bGROO?\s*\d{2,4}\b",
    r"\bHH[-\s]?AG\s*\d{3,4}\b",
    r"\bHH[-\s]?AN\s*\d{3,4}\b",
    r"\bDE[-\s]?FN\s*\d{3,4}\b",
    r"\bWI[-\s]?QY\s*\d{4}\b",
    r"\bOHA[-\s]?MX\s*\d{3}\b",
    r"\bOH[-\s]?AMX\s*\d{3}\b",
    r"\bWJQY\s*\d{4}\b",
    r"\bNGZ\s*\d{3,4}\b",
    r"\bMEC\s*\d{4,5}\b",
    r"\bMOZ[-\s]*\d{3,4}\b",
    r"\bHEI[-\s]?GW\s*\d{3,4}\b",
]

TRUCK_REFERENCE_HINTS = [
    "GR-OO***",
    "HH-AG***",
    "HH-AN***",
    "DE-FN***",
    "WI-QY****",
    "OHA-MX***",
    "WJQY****",
    "NGZ***",
    "MEC****",
    "MOZ***",
    "HEI-GW***",
]

KNOWN_TRUCK_EXAMPLES = {
    "WI-QY4010",
    "WI-QY4295",
    "OHA-MX771",
    "WJQY4010",
}


COMPACT_TRUCK_PATTERNS = [
    r"GROO\d{2,4}",
    r"GROOO\d{2,4}",
    r"GRO\d{2,4}",
    r"HHAG\d{3,4}",
    r"HHAN\d{3,4}",
    r"DEFN\d{3,4}",
    r"WIQY\d{4}",
    r"OHAMX\d{3}",
    r"WJQY\d{4}",
    r"NGZ\d{3,4}",
    r"MEC\d{4,5}",
    r"MOZ\d{3,4}",
    r"HEIGW\d{3,4}",
]


def _apply_truck_substitutions(text):
    substitutions = [
        (r"^GRO(\d{2,4})$", r"GR-OO\1"),
        (r"^GROO(\d{2,4})$", r"GR-OO\1"),
        (r"^GROOO(\d{2,4})$", r"GR-OO\1"),
        (r"^GROO(\d+)$", r"GR-OO\1"),
        (r"^GROO[-\s]*(\d{2,4})$", r"GR-OO\1"),
        (r"^GR[-\s]*OO[-\s]*(\d{2,4})$", r"GR-OO\1"),
        (r"^HHAG(\d{3,4})$", r"HH-AG\1"),
        (r"^HHAN(\d{3,4})$", r"HH-AN\1"),
        (r"^DEFN(\d{3,4})$", r"DE-FN\1"),
        (r"^WIQY(\d{4})$", r"WI-QY\1"),
        (r"^OHAMX(\d{3})$", r"OHA-MX\1"),
        (r"^OH[-\s]*AMX(\d{3})$", r"OHA-MX\1"),
        (r"^OHA[-\s]*MX(\d{3})$", r"OHA-MX\1"),
        (r"^NGZ(\d{3,4})$", r"NGZ\1"),
        (r"^MEC(\d{4,5})$", r"MEC\1"),
        (r"^MOZ[-\s]*(\d{3,4})$", r"MOZ\1"),
        (r"^HEIGW(\d{3,4})$", r"HEI-GW\1"),
        (r"^HEI[-\s]*GW(\d{3,4})$", r"HEI-GW\1"),
    ]

    for pattern, replacement in substitutions:
        text = re.sub(pattern, replacement, text)

    return text


def extract_normalized_truck_number(value):
    """Return only a normalized truck number when one can be found in mixed text."""
    if not value:
        return ""

    source = str(value).upper().strip()
    if not source:
        return ""

    for pattern in TRUCK_PREFIX_PATTERNS:
        match = re.search(pattern, source, flags=re.IGNORECASE)
        if match:
            candidate = re.sub(r"[\s-]+", "", match.group(0).upper())
            return _apply_truck_substitutions(candidate)

    compact_source = re.sub(r"[^A-Z0-9]+", "", source)
    for pattern in COMPACT_TRUCK_PATTERNS:
        match = re.search(pattern, compact_source, flags=re.IGNORECASE)
        if match:
            return _apply_truck_substitutions(match.group(0).upper())

    return ""


def strip_truck_number_from_text(value):
    """Remove truck-number fragments from free text fields such as Name."""
    text = str(value or "")
    if not text:
        return ""

    cleaned = text
    for pattern in TRUCK_PREFIX_PATTERNS:
        cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)

    return re.sub(r"\s+", " ", cleaned).strip()


def normalize_truck_candidate(value):
    """Extract and normalize a truck number to the project-friendly format."""
    if not value:
        return ""

    normalized = extract_normalized_truck_number(value)
    if normalized:
        return normalized

    source = str(value).upper().strip()
    if not source:
        return ""

    text = re.sub(r"\s+", "", source)
    text = _apply_truck_substitutions(text)

    return text


def extract_reference_trucks(text):
    """Extract truck candidates using the incomplete project truck reference."""
    if not text:
        return []

    source = str(text).upper()
    results = []
    seen = set()

    for pattern in TRUCK_PREFIX_PATTERNS:
        for match in re.finditer(pattern, source):
            candidate = normalize_truck_candidate(match.group(0))
            if candidate and candidate not in seen:
                results.append(candidate)
                seen.add(candidate)

    for candidate in KNOWN_TRUCK_EXAMPLES:
        compact_source = re.sub(r"[\s-]+", "", source)
        compact_candidate = re.sub(r"[\s-]+", "", candidate.upper())
        if compact_candidate in compact_source and candidate not in seen:
            results.append(candidate)
            seen.add(candidate)

    return results
