"""
services/llm_extraction.py
--------------------------
Phase 2: LLM-based extraction fallback.

Called by extraction.py when regex patterns produce zero observations for a source.
Uses the NVIDIA NIM API (OpenAI-compatible) with a structured-output prompt to extract
the same Observation dict format as regex extraction.

Design principles (from PROBLEM_STATEMENT.md section 6):
- Returns the same {attribute, value, unit, raw_snippet, location, extracted_by} format
  as regex extraction so arbitration.py needs zero changes.
- Gracefully degrades: if NVIDIA_API_KEY is missing or the call fails, returns []
  so the regex result (empty) is used and the pipeline continues without crashing.
- extracted_by = "llm" so the evidence ledger can show which path was used.
"""

import os
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

NVIDIA_API_BASE = "https://integrate.api.nvidia.com/v1"
LLM_MODEL = os.getenv("NVIDIA_MODEL") or os.getenv("LLM_MODEL", "meta/llama-4-scout-17b-16e-instruct")
LLM_FALLBACK_ENABLED = os.getenv("LLM_FALLBACK_ENABLED", "true").lower() == "true"

EXTRACTION_PROMPT = """You are an industrial product data extraction specialist.
Extract structured product attributes from the following raw text.

Return ONLY a valid JSON array of attribute observations. Each observation must have:
- "attribute": snake_case attribute name (e.g. "supply_voltage_rated", "weight", "operating_temp_range", "protection_rating", "work_memory", "digital_inputs")
- "value": the extracted value (number for single values, null for range-only attributes)
- "value_range": [min, max] array for range attributes, or null for scalar attributes
- "unit": unit string (e.g. "V DC", "kg", "C", "KB") or null
- "raw_snippet": the exact text substring the value was extracted from (max 80 chars)
- "location": "document" (or more specific if evident from text)
- "extracted_by": "llm"

Only include attributes you are confident about. If no product attributes are found, return [].
Do not include any explanation or markdown — just the raw JSON array.

Raw text:
{raw_text}
"""


def extract_with_llm(
    raw_text: str,
    source_id: str,
    default_location: str = "document",
) -> List[Dict[str, Any]]:
    """
    Call NVIDIA NIM to extract product attributes from raw text.
    Returns a list of Observation dicts (same format as extraction.py).
    Returns [] on any failure so the pipeline degrades gracefully.
    """
    if not LLM_FALLBACK_ENABLED:
        return []

    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        logger.warning("LLM fallback triggered but NVIDIA_API_KEY not set — skipping.")
        return []

    try:
        import httpx
    except ImportError:
        logger.warning("httpx not installed — LLM fallback unavailable.")
        return []

    prompt = EXTRACTION_PROMPT.format(raw_text=raw_text[:6000])  # cap at 6k chars

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                f"{NVIDIA_API_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": LLM_MODEL,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 1024,
                },
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()

        # Strip markdown code fences if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        raw_obs = json.loads(content)
        if not isinstance(raw_obs, list):
            logger.warning("LLM returned non-list JSON — skipping.")
            return []

        # Validate and normalise each observation
        valid = []
        for o in raw_obs:
            if not isinstance(o, dict) or "attribute" not in o:
                continue
            valid.append({
                "attribute": str(o["attribute"]),
                "value": o.get("value"),
                "value_range": o.get("value_range"),  # list [min, max] or null
                "unit": o.get("unit"),
                "raw_snippet": str(o.get("raw_snippet", ""))[:120],
                "location": str(o.get("location", default_location)),
                "extracted_by": "llm",
            })

        logger.info(f"LLM extracted {len(valid)} observations from {source_id}")
        return valid

    except Exception as e:
        logger.warning(f"LLM extraction failed for {source_id}: {e}")
        return []
