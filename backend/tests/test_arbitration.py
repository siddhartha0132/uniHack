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
