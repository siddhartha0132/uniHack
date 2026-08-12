from app.extraction import extract_from_text, extract_from_csv

def test_extract_from_text():
    text = "Weight: 1.25 kg. Supply voltage: 24 V DC."
    obs = extract_from_text(text, source_id="test")
    
    weights = [o for o in obs if o["attribute"] == "weight"]
    voltages = [o for o in obs if o["attribute"] == "supply_voltage_rated"]
    
    assert len(weights) == 1
    assert weights[0]["value"] == 1.25
    assert weights[0]["unit"] == "kg"
    
    assert len(voltages) == 1
    assert voltages[0]["value"] == 24.0

def test_extract_from_csv():
    csv_content = "sku,voltage,weight_kg,protection\nABC,24V DC,1.5,IP67"
    obs = extract_from_csv(csv_content, source_id="csv_test")
    
    assert len(obs) == 3
    
    weights = [o for o in obs if o["attribute"] == "weight"]
    assert weights[0]["value"] == 1.5
    
    protection = [o for o in obs if o["attribute"] == "protection_rating"]
    assert protection[0]["value"] == "IP67"
