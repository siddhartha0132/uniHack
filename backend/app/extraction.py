"""
extraction.py
-------------
Turns raw source documents (plain text extracted from PDFs/web pages, or CSV rows)
into candidate attribute observations: {attribute, value, unit, raw_snippet, location}.

This module is intentionally pattern-based (regex) so the whole pipeline runs with
zero external API calls and is fully inspectable/demoable offline. In production this
is the layer that gets replaced/augmented with an LLM + vision-language model call —
see STATUS_AND_ROADMAP.md, "Swap-in points", item 1.

Each function returns a list of "Observation" dicts:
{
    "attribute": "supply_voltage",       # normalized attribute key
    "value": 24.0,                       # normalized numeric value (or string)
    "value_range": (20.4, 28.8) | None,  # optional range
    "unit": "V DC",
    "raw_snippet": "...",                # exact text the value was pulled from (for evidence)
    "location": "Page 24" | "CSV row 1" | "Product page",
    "extracted_by": "regex" | "llm",    # tracks which extraction path was used
}
"""

import re
import csv
import io
from typing import List, Dict, Any


def _obs(attribute, value, unit, raw_snippet, location, value_range=None, extracted_by="regex"):
    return {
        "attribute": attribute,
        "value": value,
        "value_range": value_range,
        "unit": unit,
        "raw_snippet": raw_snippet.strip(),
        "location": location,
        "extracted_by": extracted_by,
    }


# Each pattern: (attribute_key, regex, unit, group_handling)
TEXT_PATTERNS = [
    (
        "supply_voltage_rated",
        re.compile(r"(?:Supply voltage|Input voltage)[:\s]*(?:rated\s*)?(\d+(?:\.\d+)?)\s*V\s*DC", re.I),
        "V DC",
    ),
    (
        "supply_voltage_rated",
        re.compile(r"(?:operating range|Operating temperature range)?\s*(\d+\.?\d*)\s*V\s*DC\s*to\s*(\d+\.?\d*)\s*V\s*DC", re.I),
        "V DC",
    ),
    (
        "weight",
        re.compile(r"Weight[:\s]*(?:approximately\s*)?(\d+(?:\.\d+)?)\s*kg", re.I),
        "kg",
    ),
    (
        "operating_temp_range",
        re.compile(r"(?:Ambient temperature during operation|Operating temperature)[:\s]*(-?\d+(?:\.\d+)?)\s*C?\s*to\s*\+?(-?\d+(?:\.\d+)?)\s*C", re.I),
        "C",
    ),
    (
        "protection_rating",
        re.compile(r"(?:Degree of protection|Protection class)[:\s]*(IP\d{2})", re.I),
        None,
    ),
    (
        "work_memory",
        re.compile(r"(?:Work memory|Memory)[:\s]*(\d+)\s*KB", re.I),
        "KB",
    ),
    (
        "digital_inputs",
        re.compile(r"(\d+)\s*x?\s*(?:24\s*V\s*DC)?\s*(?:Digital inputs|DI)\b", re.I),
        "count",
    ),
]


def extract_from_text(raw_text: str, source_id: str, default_location: str = "document") -> List[Dict[str, Any]]:
    observations = []

    for attr, pattern, unit in TEXT_PATTERNS:
        for m in pattern.finditer(raw_text):
            snippet_start = max(0, m.start() - 20)
            snippet_end = min(len(raw_text), m.end() + 20)
            raw_snippet = raw_text[snippet_start:snippet_end]

            if attr == "supply_voltage_rated":
                # Check if pattern has 2 groups (range) or 1 group (single value)
                if m.lastindex == 2:
                    observations.append(_obs(
                        "supply_voltage_rated", None, unit, raw_snippet, default_location,
                        value_range=(float(m.group(1)), float(m.group(2)))
                    ))
                else:
                    observations.append(_obs("supply_voltage_rated", float(m.group(1)), unit, raw_snippet, default_location))
            elif attr == "operating_temp_range":
                observations.append(_obs(
                    "operating_temp_range", None, unit, raw_snippet, default_location,
                    value_range=(float(m.group(1)), float(m.group(2)))
                ))
            elif attr == "protection_rating":
                observations.append(_obs(attr, m.group(1).upper(), unit, raw_snippet, default_location))
            elif attr in ("weight", "work_memory", "digital_inputs"):
                observations.append(_obs(attr, float(m.group(1)), unit, raw_snippet, default_location))

    # Page/location hint if present near the top of the document
    page_match = re.search(r"Page\s+(\d+)", raw_text, re.I)
    if page_match:
        for o in observations:
            if o["location"] == default_location:
                o["location"] = f"Page {page_match.group(1)}"

    # Phase 2: LLM fallback — if regex found nothing, ask the LLM
    if not observations:
        try:
            from .services.llm_extraction import extract_with_llm
            llm_obs = extract_with_llm(raw_text, source_id, default_location)
            observations.extend(llm_obs)
        except Exception:
            pass  # Never crash the pipeline on LLM fallback failure

    return observations


def extract_from_csv(raw_csv: str, source_id: str) -> List[Dict[str, Any]]:
    observations = []
    reader = csv.DictReader(io.StringIO(raw_csv))
    for row_idx, row in enumerate(reader, start=1):
        location = f"CSV row {row_idx}"

        if "voltage" in row and row["voltage"]:
            v = re.search(r"(\d+(?:\.\d+)?)", row["voltage"])
            if v:
                observations.append(_obs("supply_voltage_rated", float(v.group(1)), "V DC", row["voltage"], location))

        if "weight_kg" in row and row["weight_kg"]:
            observations.append(_obs("weight", float(row["weight_kg"]), "kg", row["weight_kg"], location))

        if "temp_range" in row and row["temp_range"]:
            m = re.search(r"(-?\d+(?:\.\d+)?)\s*to\s*(-?\d+(?:\.\d+)?)", row["temp_range"])
            if m:
                observations.append(_obs(
                    "operating_temp_range", None, "C", row["temp_range"], location,
                    value_range=(float(m.group(1)), float(m.group(2)))
                ))

        if "protection" in row and row["protection"]:
            observations.append(_obs("protection_rating", row["protection"].upper(), None, row["protection"], location))

        if "memory_kb" in row and row["memory_kb"]:
            observations.append(_obs("work_memory", float(row["memory_kb"]), "KB", row["memory_kb"], location))

    return observations


# ---------------------------------------------------------------------------
# Phase 1 — PDF extraction via PyMuPDF
# ---------------------------------------------------------------------------

def extract_from_pdf_bytes(pdf_bytes: bytes, source_id: str) -> List[Dict[str, Any]]:
    """
    Extract attribute observations from a PDF file's raw bytes.
    Uses PyMuPDF (fitz) to convert each page to plain text, then runs the
    standard regex pattern matching on each page individually so location
    hints include the actual page number.

    If PyMuPDF is not installed (optional dependency), raises ImportError
    with a clear message.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError(
            "PyMuPDF is required for PDF extraction. Install it: pip install pymupdf"
        )

    observations: List[Dict[str, Any]] = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    for page_num in range(len(doc)):
        page: Any = doc[page_num]
        text = page.get_text("text")
        location = f"Page {page_num + 1}"
        page_obs = extract_from_text(text, source_id, default_location=location)
        # Override location with the real page number
        for o in page_obs:
            o["location"] = location
        observations.extend(page_obs)

    doc.close()
    return observations
