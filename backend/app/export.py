"""
export.py
---------
Phase 4: PIM export connectors.

Converts a processed product record to formats industrial PIM/ERP systems
can ingest directly. Starting with two formats:
  - generic_json: clean, flat JSON with resolved values + confidence (simplest)
  - akeneo_csv:   Akeneo-style CSV import format (most common B2B PIM target)

Adding new formats: implement a new `to_<format>()` function and register it
in EXPORT_FORMATS at the bottom.
"""

import csv
import io
import json
from typing import Dict, Any


def to_generic_json(record: Dict[str, Any]) -> str:
    """
    Export as clean, flat JSON: only resolved values + confidence per attribute.
    Strips internal fields (evidence list, reasoning) so the export is concise
    enough for direct API consumption by downstream PIM/ERP systems.
    """
    output = {
        "product_id":   record["product_id"],
        "product_name": record["product_name"],
        "data_quality": {
            "overall_score":     record["quality"]["overall_score"],
            "completeness_pct":  record["quality"]["completeness"],
            "avg_confidence_pct": record["quality"]["avg_confidence"],
        },
        "attributes": {},
    }

    if record.get("classification"):
        cls = record["classification"]
        output["classification"] = {
            "etim":   cls.get("etim_class"),
            "eclass": cls.get("eclass_code"),
            "unspsc": cls.get("unspsc"),
        }

    for attr_name, attr_data in record.get("attributes", {}).items():
        val = attr_data.get("resolved_value")
        output["attributes"][attr_name] = {
            "value":      val,
            "unit":       attr_data.get("unit"),
            "confidence": attr_data.get("confidence"),
            "status":     attr_data.get("status"),
        }

    return json.dumps(output, indent=2, default=str)


def to_akeneo_csv(record: Dict[str, Any]) -> str:
    """
    Export as Akeneo-compatible CSV.
    Columns: sku, name, categories, weight, supply_voltage, operating_temp_min,
             operating_temp_max, protection_rating, work_memory, digital_inputs,
             etim_class, eclass_code, unspsc, data_quality_score

    Akeneo's importer expects one row per product variant; units are embedded
    in column headers per Akeneo convention (e.g. weight-kg).
    """
    fieldnames = [
        "sku",
        "name",
        "weight-kg",
        "supply_voltage-V DC",
        "operating_temp_min-C",
        "operating_temp_max-C",
        "protection_rating",
        "work_memory-KB",
        "digital_inputs",
        "etim_class",
        "eclass_code",
        "unspsc",
        "data_quality_score",
    ]

    attrs = record.get("attributes", {})

    def get_val(key, default=""):
        a = attrs.get(key)
        if not a:
            return default
        v = a.get("resolved_value")
        if v is None:
            return default
        return v

    def get_range_min(key):
        a = attrs.get(key)
        if not a:
            return ""
        v = a.get("resolved_value")
        if isinstance(v, (list, tuple)) and len(v) == 2:
            return v[0]
        return ""

    def get_range_max(key):
        a = attrs.get(key)
        if not a:
            return ""
        v = a.get("resolved_value")
        if isinstance(v, (list, tuple)) and len(v) == 2:
            return v[1]
        return ""

    cls = record.get("classification") or {}

    row = {
        "sku":                   record["product_id"],
        "name":                  record["product_name"],
        "weight-kg":             get_val("weight"),
        "supply_voltage-V DC":   get_val("supply_voltage_rated"),
        "operating_temp_min-C":  get_range_min("operating_temp_range"),
        "operating_temp_max-C":  get_range_max("operating_temp_range"),
        "protection_rating":     get_val("protection_rating"),
        "work_memory-KB":        get_val("work_memory"),
        "digital_inputs":        get_val("digital_inputs"),
        "etim_class":            cls.get("etim_class", ""),
        "eclass_code":           cls.get("eclass_code", ""),
        "unspsc":                cls.get("unspsc", ""),
        "data_quality_score":    record["quality"]["overall_score"],
    }

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerow(row)
    return buf.getvalue()


EXPORT_FORMATS = {
    "json":       ("application/json",      "veritas_export.json", to_generic_json),
    "akeneo_csv": ("text/csv",              "akeneo_import.csv",   to_akeneo_csv),
}


def export_product(record: Dict[str, Any], fmt: str):
    """
    Returns (content_type, filename, content_str).
    Raises ValueError for unknown formats.
    """
    if fmt not in EXPORT_FORMATS:
        raise ValueError(
            f"Unknown export format '{fmt}'. Valid: {', '.join(EXPORT_FORMATS)}"
        )
    content_type, filename, fn = EXPORT_FORMATS[fmt]
    return content_type, filename, fn(record)
