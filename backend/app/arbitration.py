"""
arbitration.py
---------------
This is the core of the product. Extraction (pulling candidate values out of documents)
is commodity — every LLM can do it. Deciding WHICH of several disagreeing sources to
trust, HOW confident to be, and WHY, is the defensible part.

Input: observations grouped by source, each source tagged with a source_type
       (datasheet / manufacturer_website / distributor_erp / image_label / catalog_pdf)
Output: per-attribute resolved record with:
    - resolved_value
    - confidence (0-1)
    - status: "agreed" | "resolved_conflict" | "unresolved_conflict" | "single_source"
    - evidence: list of {source_id, source_type, location, raw_snippet, value}
    - reasoning: human-readable explanation of why this value was chosen

This weighting table is a starting point — see STATUS_AND_ROADMAP.md item 3
("learned reliability weights") for how this becomes a live, per-customer model
that improves as humans correct it, instead of a static table.
"""

from typing import List, Dict, Any
from collections import defaultdict

# Static prior on how much to trust each source TYPE before any customer feedback exists.
SOURCE_RELIABILITY = {
    "datasheet": 0.95,
    "image_label": 0.90,
    "manufacturer_website": 0.75,
    "catalog_pdf": 0.70,
    "distributor_erp": 0.55,
    "unknown": 0.40,
}

# How much two numeric values are allowed to differ (relative) before it's a "conflict"
# rather than noise/rounding.
NUMERIC_TOLERANCE = 0.08  # 8%


def _values_agree(a, b, tolerance=NUMERIC_TOLERANCE) -> bool:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if a == 0 and b == 0:
            return True
        denom = max(abs(a), abs(b), 1e-9)
        return abs(a - b) / denom <= tolerance
    return str(a).strip().lower() == str(b).strip().lower()


def _range_agree(r1, r2, tolerance=NUMERIC_TOLERANCE) -> bool:
    return _values_agree(r1[0], r2[0], tolerance) and _values_agree(r1[1], r2[1], tolerance)


def arbitrate(observations_by_source: Dict[str, Dict[str, Any]],
              reliability_overrides: Dict[str, float] = None) -> Dict[str, Any]:
    """
    observations_by_source: {
        "source_a": {"source_type": "datasheet", "observations": [ {...}, ... ]},
        "source_b": {"source_type": "manufacturer_website", "observations": [ {...}, ... ]},
        ...
    }
    reliability_overrides: optional dict of {source_type: float} — Phase 5 learned weights.
    When provided, merged with SOURCE_RELIABILITY (overrides win for types that appear in both).

    Returns: {attribute_name: resolved_record}
    """
    # Merge static prior with learned weights (Phase 5)
    effective_reliability = dict(SOURCE_RELIABILITY)
    if reliability_overrides:
        effective_reliability.update(reliability_overrides)

    # 1. group all observations of the same attribute across sources
    by_attribute = defaultdict(list)
    for source_id, source_data in observations_by_source.items():
        source_type = source_data.get("source_type", "unknown")
        reliability = effective_reliability.get(source_type, effective_reliability["unknown"])
        for obs in source_data.get("observations", []):
            by_attribute[obs["attribute"]].append({
                **obs,
                "source_id": source_id,
                "source_type": source_type,
                "reliability": reliability,
            })

    resolved = {}

    for attribute, obs_list in by_attribute.items():
        is_range = obs_list[0].get("value_range") is not None
        key = "value_range" if is_range else "value"

        # sort candidates by source reliability, highest first
        obs_list_sorted = sorted(obs_list, key=lambda o: o["reliability"], reverse=True)
        top = obs_list_sorted[0]

        # partition into agreeing / disagreeing with the top (most trusted) source
        agree_fn = _range_agree if is_range else _values_agree
        agreeing = [o for o in obs_list_sorted if agree_fn(o[key], top[key])]
        disagreeing = [o for o in obs_list_sorted if not agree_fn(o[key], top[key])]

        evidence = [
            {
                "source_id": o["source_id"],
                "source_type": o["source_type"],
                "location": o["location"],
                "raw_snippet": o["raw_snippet"],
                "value": o[key],
                "unit": o.get("unit"),
                "agrees_with_resolution": o in agreeing,
            }
            for o in obs_list_sorted
        ]

        if len(obs_list_sorted) == 1:
            status = "single_source"
            confidence = round(top["reliability"] * 0.85, 2)  # slightly discounted: no corroboration
            reasoning = (
                f"Only one source ({top['source_type']}, {top['location']}) reports this attribute. "
                f"No corroboration available — confidence capped below multi-source agreement levels."
            )
        elif not disagreeing:
            status = "agreed"
            avg_reliability = sum(o["reliability"] for o in obs_list_sorted) / len(obs_list_sorted)
            # more agreeing sources -> higher confidence, with diminishing returns
            corroboration_bonus = min(0.15, 0.05 * (len(obs_list_sorted) - 1))
            confidence = round(min(0.99, avg_reliability + corroboration_bonus), 2)
            reasoning = (
                f"{len(obs_list_sorted)} sources agree within tolerance "
                f"({', '.join(o['source_type'] for o in obs_list_sorted)})."
            )
        else:
            # conflict — resolve to the highest-reliability source, but confidence takes a real hit
            status = "resolved_conflict"
            reliability_gap = top["reliability"] - max((o["reliability"] for o in disagreeing), default=0)
            confidence = round(max(0.35, min(0.90, top["reliability"] - 0.20 + reliability_gap * 0.2)), 2)
            other_desc = "; ".join(
                f"{o['source_type']} reports {o[key]}{(' ' + o['unit']) if o.get('unit') else ''}"
                for o in disagreeing
            )
            reasoning = (
                f"Conflict detected. Resolved to {top['source_type']} "
                f"({top['location']}) as the highest-reliability source. "
                f"Disagreeing: {other_desc}."
            )
            if confidence < 0.60:
                status = "unresolved_conflict"
                reasoning += " Confidence too low for auto-publish — routed to human review."

        resolved[attribute] = {
            "resolved_value": top[key],
            "unit": top.get("unit"),
            "status": status,
            "confidence": confidence,
            "reasoning": reasoning,
            "evidence": evidence,
        }

    return resolved


def compute_quality_score(resolved: Dict[str, Any], expected_attributes: List[str]) -> Dict[str, Any]:
    """
    Rolls up per-attribute confidence into a single product-level quality score,
    with an explanation — this is what gets shown as the headline number in the UI.
    """
    found = list(resolved.keys())
    completeness = round(100 * len(found) / max(1, len(expected_attributes)), 1)

    if resolved:
        avg_confidence = round(100 * sum(r["confidence"] for r in resolved.values()) / len(resolved), 1)
    else:
        avg_confidence = 0.0

    conflicts = [a for a, r in resolved.items() if r["status"] in ("resolved_conflict", "unresolved_conflict")]
    needs_review = [a for a, r in resolved.items() if r["status"] == "unresolved_conflict" or r["confidence"] < 0.75]

    overall = round(0.5 * completeness + 0.5 * avg_confidence, 1)

    missing = [a for a in expected_attributes if a not in found]

    explanation = (
        f"{len(found)}/{len(expected_attributes)} expected attributes found. "
        f"{len(resolved) - len(conflicts)}/{len(resolved)} attributes agreed across sources without conflict. "
        f"{len(conflicts)} conflict(s) detected and resolved by source reliability. "
        f"{len(needs_review)} attribute(s) flagged for human review."
    )

    return {
        "overall_score": overall,
        "completeness": completeness,
        "avg_confidence": avg_confidence,
        "conflicts_detected": len(conflicts),
        "needs_review": needs_review,
        "missing_attributes": missing,
        "explanation": explanation,
    }
