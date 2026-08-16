import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.arbitration import arbitrate, compute_quality_score, SOURCE_RELIABILITY

def test_arbitration_agreed():
    observations_by_source = {
        "source_a": {
            "source_type": "datasheet",
            "observations": [
                {"attribute": "weight", "value": 1.2, "unit": "kg", "raw_snippet": "1.2kg", "location": "Page 1"}
            ]
        },
        "source_b": {
            "source_type": "manufacturer_website",
            "observations": [
                {"attribute": "weight", "value": 1.2, "unit": "kg", "raw_snippet": "1.2 kg", "location": "Web"}
            ]
        }
    }
    
    resolved = arbitrate(observations_by_source)
    assert "weight" in resolved
    assert resolved["weight"]["resolved_value"] == 1.2
    assert resolved["weight"]["status"] == "agreed"
    assert resolved["weight"]["confidence"] == 0.90

def test_arbitration_conflict():
    observations_by_source = {
        "source_a": {
            "source_type": "datasheet",
            "observations": [
                {"attribute": "weight", "value": 1.5, "unit": "kg", "raw_snippet": "1.5kg", "location": "Page 1"}
            ]
        },
        "source_b": {
            "source_type": "distributor_erp",
            "observations": [
                {"attribute": "weight", "value": 1.2, "unit": "kg", "raw_snippet": "1.2", "location": "Row 1"}
            ]
        }
    }
    
    resolved = arbitrate(observations_by_source)
    assert resolved["weight"]["resolved_value"] == 1.5
    assert resolved["weight"]["status"] == "resolved_conflict"
    assert resolved["weight"]["confidence"] < SOURCE_RELIABILITY["datasheet"] # Conflict penalty

def test_arbitration_tolerance():
    # 1.2 and 1.25 should be within 8% tolerance (1.25-1.2)/1.25 = 0.04
    observations_by_source = {
        "source_a": {
            "source_type": "datasheet",
            "observations": [
                {"attribute": "weight", "value": 1.25, "unit": "kg", "raw_snippet": "1.25kg", "location": "Page 1"}
            ]
        },
        "source_b": {
            "source_type": "manufacturer_website",
            "observations": [
                {"attribute": "weight", "value": 1.2, "unit": "kg", "raw_snippet": "1.2 kg", "location": "Web"}
            ]
        }
    }
    
    resolved = arbitrate(observations_by_source)
    assert resolved["weight"]["status"] == "agreed"


# ─── Quality score tests ─────────────────────────────────────────────────

EXPECTED = ["supply_voltage_rated", "weight", "operating_temp_range",
            "protection_rating", "work_memory", "digital_inputs"]


def _make_attr(value, confidence, status="agreed"):
    return {
        "resolved_value": value,
        "unit": "kg",
        "confidence": confidence,
        "status": status,
        "reasoning": "test",
        "evidence": [],
    }


def test_quality_score_full_completeness():
    """All expected attributes present with high confidence."""
    resolved = {attr: _make_attr(1.0, 0.95) for attr in EXPECTED}
    q = compute_quality_score(resolved, EXPECTED)
    assert q["completeness"] == 100.0
    assert q["missing_attributes"] == []
    assert q["overall_score"] > 90


def test_quality_score_partial_missing():
    """Only half the expected attributes present."""
    resolved = {attr: _make_attr(1.0, 0.90) for attr in EXPECTED[:3]}
    q = compute_quality_score(resolved, EXPECTED)
    assert q["completeness"] == 50.0
    assert set(q["missing_attributes"]) == set(EXPECTED[3:])


def test_quality_score_flags_conflicts():
    """Attributes with resolved_conflict status are counted."""
    resolved = {
        "weight": _make_attr(1.5, 0.70, "resolved_conflict"),
        "supply_voltage_rated": _make_attr(24.0, 0.95, "agreed"),
    }
    q = compute_quality_score(resolved, EXPECTED)
    assert q["conflicts_detected"] == 1


def test_quality_score_needs_review_low_confidence():
    """Attributes below 0.75 confidence are flagged for review."""
    resolved = {
        "weight": _make_attr(1.5, 0.50, "unresolved_conflict"),
        "supply_voltage_rated": _make_attr(24.0, 0.95, "agreed"),
    }
    q = compute_quality_score(resolved, EXPECTED)
    assert "weight" in q["needs_review"]
    assert "supply_voltage_rated" not in q["needs_review"]


def test_quality_score_empty():
    """No attributes at all."""
    q = compute_quality_score({}, EXPECTED)
    assert q["completeness"] == 0.0
    assert q["avg_confidence"] == 0.0
    assert q["overall_score"] == 0.0
    assert len(q["missing_attributes"]) == len(EXPECTED)
