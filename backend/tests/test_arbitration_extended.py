"""
Extended tests for arbitration and extraction modules.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app.arbitration import arbitrate, compute_quality_score, _values_agree, _range_agree
from app.extraction import extract_from_text, _obs


class TestArbitrationCore:
    """Tests for core arbitration logic."""

    def test_values_agree_numeric_tolerance(self):
        """Test numeric agreement within 8% tolerance."""
        assert _values_agree(24.0, 24.0) is True
        assert _values_agree(24.0, 24.1) is True  # within 8%
        assert _values_agree(24.0, 25.0) is True  # within 8%
        # 24 to 26: diff=2, max=26, ratio=2/26=7.69% < 8% -> True
        assert _values_agree(24.0, 26.0) is True  
        # 24 to 27: diff=3, max=27, ratio=3/27=11.1% > 8% -> False
        assert _values_agree(24.0, 27.0) is False
        assert _values_agree(0, 0) is True

    def test_values_agree_string_exact(self):
        """Test string agreement requires exact match."""
        assert _values_agree("IP20", "IP20") is True
        assert _values_agree("IP20", "ip20") is True  # case insensitive
        assert _values_agree("IP20", "IP21") is False

    def test_range_agree(self):
        """Test range agreement."""
        assert _range_agree((20.0, 28.0), (20.4, 28.8)) is True
        assert _range_agree((20.0, 28.0), (20.0, 28.0)) is True
        assert _range_agree((20.0, 28.0), (15.0, 25.0)) is False

    def _make_obs(self, attr, value, unit, reliability, source_type="datasheet", source_id="src1"):
        """Helper to create observation dict with required fields."""
        return {
            "attribute": attr,
            "value": value,
            "unit": unit,
            "reliability": reliability,
            "source_id": source_id,
            "source_type": source_type,
            "location": "test_location",
            "raw_snippet": "test snippet",
        }

    def test_arbitrate_single_source(self):
        """Test arbitration with single source."""
        obs = {"src1": {"source_type": "datasheet", "observations": [
            self._make_obs("weight", 1.5, "kg", 0.95)
        ]}}
        result = arbitrate(obs)
        assert result["weight"]["status"] == "single_source"
        assert result["weight"]["confidence"] == 0.81  # 0.95 * 0.85

    def test_arbitrate_agreed(self):
        """Test arbitration with agreeing sources."""
        obs = {
            "src1": {"source_type": "datasheet", "observations": [
                self._make_obs("weight", 1.5, "kg", 0.95, "datasheet", "src1")
            ]},
            "src2": {"source_type": "manufacturer_website", "observations": [
                self._make_obs("weight", 1.52, "kg", 0.75, "manufacturer_website", "src2")
            ]},
        }
        result = arbitrate(obs)
        assert result["weight"]["status"] == "agreed"
        assert result["weight"]["confidence"] > 0.8

    def test_arbitrate_conflict(self):
        """Test arbitration with conflicting sources."""
        obs = {
            "src1": {"source_type": "datasheet", "observations": [
                self._make_obs("weight", 1.5, "kg", 0.95, "datasheet", "src1")
            ]},
            "src2": {"source_type": "distributor_erp", "observations": [
                self._make_obs("weight", 1.0, "kg", 0.55, "distributor_erp", "src2")
            ]},
        }
        result = arbitrate(obs)
        assert result["weight"]["status"] in ("resolved_conflict", "unresolved_conflict")
        assert result["weight"]["resolved_value"] == 1.5  # higher reliability wins

    def test_compute_quality_score_complete(self):
        """Test quality score with all expected attributes."""
        resolved = {
            "weight": {"confidence": 0.9, "status": "agreed"},
            "voltage": {"confidence": 0.8, "status": "resolved_conflict"},
            "temp": {"confidence": 0.85, "status": "agreed"},
        }
        expected = ["weight", "voltage", "temp"]
        score = compute_quality_score(resolved, expected)
        assert score["completeness"] == 100.0
        assert score["conflicts_detected"] == 1
        # voltage has status=resolved_conflict (not unresolved_conflict) and confidence=0.8 >= 0.75
        # so it should NOT be in needs_review
        assert score["needs_review"] == []

    def test_compute_quality_score_partial(self):
        """Test quality score with missing attributes."""
        resolved = {
            "weight": {"confidence": 0.9, "status": "agreed"},
        }
        expected = ["weight", "voltage", "temp"]
        score = compute_quality_score(resolved, expected)
        assert score["completeness"] == pytest.approx(33.3, rel=0.1)
        assert score["missing_attributes"] == ["voltage", "temp"]


class TestExtraction:
    """Tests for extraction module."""

    def test_obs_creation(self):
        """Test observation creation helper."""
        obs = _obs("weight", 1.5, "kg", "Weight: 1.5 kg", "Page 1")
        assert obs["attribute"] == "weight"
        assert obs["value"] == 1.5
        assert obs["unit"] == "kg"
        assert obs["value_range"] is None
        assert obs["extracted_by"] == "regex"

    def test_obs_with_range(self):
        """Test observation with value range."""
        obs = _obs("voltage", None, "V DC", "20.4 to 28.8 V DC", "Page 1", value_range=(20.4, 28.8))
        assert obs["value"] is None
        assert obs["value_range"] == (20.4, 28.8)
        assert isinstance(obs["value_range"], tuple)

    def test_extract_voltage_rated(self):
        """Test extraction of supply voltage rated."""
        text = "Supply voltage rated 24 V DC"
        obs = extract_from_text(text, "test_src")
        voltage_obs = [o for o in obs if o["attribute"] == "supply_voltage_rated"]
        assert len(voltage_obs) == 1
        assert voltage_obs[0]["value"] == 24.0
        assert voltage_obs[0]["unit"] == "V DC"

    def test_extract_voltage_range(self):
        """Test extraction of supply voltage range."""
        text = "Operating range 20.4 V DC to 28.8 V DC"
        obs = extract_from_text(text, "test_src")
        voltage_obs = [o for o in obs if o["attribute"] == "supply_voltage_rated" and o["value_range"]]
        assert len(voltage_obs) == 1
        assert voltage_obs[0]["value_range"] == (20.4, 28.8)
        assert voltage_obs[0]["value"] is None

    def test_extract_weight(self):
        """Test extraction of weight."""
        text = "Weight: 1.5 kg"
        obs = extract_from_text(text, "test_src")
        weight_obs = [o for o in obs if o["attribute"] == "weight"]
        assert len(weight_obs) == 1
        assert weight_obs[0]["value"] == 1.5
        assert weight_obs[0]["unit"] == "kg"

    def test_extract_temperature_range(self):
        """Test extraction of temperature range."""
        text = "Operating temperature -20 C to +60 C"
        obs = extract_from_text(text, "test_src")
        temp_obs = [o for o in obs if o["attribute"] == "operating_temp_range"]
        assert len(temp_obs) == 1
        assert temp_obs[0]["value_range"] == (-20.0, 60.0)

    def test_extract_protection_rating(self):
        """Test extraction of protection rating."""
        text = "Degree of protection: IP20"
        obs = extract_from_text(text, "test_src")
        prot_obs = [o for o in obs if o["attribute"] == "protection_rating"]
        assert len(prot_obs) == 1
        assert prot_obs[0]["value"] == "IP20"

    def test_extract_work_memory(self):
        """Test extraction of work memory."""
        text = "Work memory 125 KB"
        obs = extract_from_text(text, "test_src")
        mem_obs = [o for o in obs if o["attribute"] == "work_memory"]
        assert len(mem_obs) == 1
        assert mem_obs[0]["value"] == 125.0
        assert mem_obs[0]["unit"] == "KB"

    def test_extract_digital_inputs(self):
        """Test extraction of digital inputs."""
        text = "14 x 24 V DC Digital inputs"
        obs = extract_from_text(text, "test_src")
        di_obs = [o for o in obs if o["attribute"] == "digital_inputs"]
        assert len(di_obs) == 1
        assert di_obs[0]["value"] == 14.0
        assert di_obs[0]["unit"] == "count"

    def test_page_location_hint(self):
        """Test page location hint extraction."""
        text = "Page 3\nSupply voltage rated 24 V DC"
        obs = extract_from_text(text, "test_src")
        assert all(o["location"] == "Page 3" for o in obs)


class TestNormalization:
    """Tests for value normalization."""

    def _make_obs(self, attr, value, unit, reliability, source_type="datasheet", source_id="src1"):
        """Helper to create observation dict with required fields."""
        return {
            "attribute": attr,
            "value": value,
            "unit": unit,
            "reliability": reliability,
            "source_id": source_id,
            "source_type": source_type,
            "location": "test_location",
            "raw_snippet": "test snippet",
        }

    def test_arbitration_uses_correct_reliability(self):
        """Test that arbitration uses correct source reliability."""
        obs = {
            "src1": {"source_type": "datasheet", "observations": [
                self._make_obs("weight", 1.5, "kg", 0.95, "datasheet", "src1")
            ]},
            "src2": {"source_type": "distributor_erp", "observations": [
                self._make_obs("weight", 2.0, "kg", 0.55, "distributor_erp", "src2")
            ]},
        }
        result = arbitrate(obs)
        # datasheet has higher reliability (0.95) so it should win
        assert result["weight"]["resolved_value"] == 1.5