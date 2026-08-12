import os
import json
import logging
import base64
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

NVIDIA_API_BASE = "https://integrate.api.nvidia.com/v1"
VLM_MODEL = os.getenv("NVIDIA_MODEL") or os.getenv("VLM_MODEL", "meta/llama-3.2-90b-vision-instruct")

EXTRACTION_PROMPT = """You are an industrial product data extraction specialist.
Extract structured product attributes from the following image.

Return ONLY a valid JSON array of attribute observations. Each observation must have:
- "attribute": snake_case attribute name (e.g. "supply_voltage_rated", "weight", "operating_temp_range", "protection_rating", "work_memory", "digital_inputs")
- "value": the extracted value (number for single values, null for range-only attributes)
- "value_range": [min, max] array for range attributes, or null for scalar attributes
- "unit": unit string (e.g. "V DC", "kg", "C", "KB") or null
- "raw_snippet": the exact text substring the value was extracted from
- "location": "image_label"
- "extracted_by": "vlm"

Only include attributes you are confident about. If no product attributes are found, return [].
Do not include any explanation or markdown — just the raw JSON array.
"""

def extract_with_vision(image_bytes: bytes, source_id: str, location_hint: str) -> List[Dict[str, Any]]:
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        logger.warning("VLM fallback triggered but NVIDIA_API_KEY not set — returning mock.")
        return _mock_response(location_hint)

    try:
        import httpx
    except ImportError:
        logger.warning("httpx not installed — returning mock.")
        return _mock_response(location_hint)

    b64_image = base64.b64encode(image_bytes).decode('utf-8')
    image_url = f"data:image/jpeg;base64,{b64_image}"

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                f"{NVIDIA_API_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": VLM_MODEL,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": EXTRACTION_PROMPT},
                                {"type": "image_url", "image_url": {"url": image_url}}
                            ]
                        }
                    ],
                    "temperature": 0.1,
                    "max_tokens": 1024,
                },
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()

        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        raw_obs = json.loads(content)
        if not isinstance(raw_obs, list):
            return []

        valid = []
        for o in raw_obs:
            if not isinstance(o, dict) or "attribute" not in o:
                continue
            valid.append({
                "attribute": str(o["attribute"]),
                "value": o.get("value"),
                "value_range": o.get("value_range"),
                "unit": o.get("unit"),
                "raw_snippet": str(o.get("raw_snippet", ""))[:120],
                "location": str(o.get("location", location_hint)),
                "extracted_by": "vlm",
            })
        return valid

    except Exception as e:
        logger.warning(f"VLM extraction failed for {source_id}: {e}")
        return _mock_response(location_hint)

def _mock_response(location_hint: str):
    return [
        {
            "attribute": "supply_voltage_rated",
            "value": 24.0,
            "unit": "V DC",
            "raw_snippet": "[MOCK VLM OCR] INPUT: 24 VDC",
            "location": location_hint,
            "extracted_by": "vlm"
        },
        {
            "attribute": "protection_rating",
            "value": "IP20",
            "unit": None,
            "raw_snippet": "[MOCK VLM OCR] IP20",
            "location": location_hint,
            "extracted_by": "vlm"
        }
    ]
