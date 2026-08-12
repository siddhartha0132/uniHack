"""
classification.py
------------------
Maps a product to industrial classification standards (ETIM, ECLASS, UNSPSC).
This is a secondary differentiator versus generic PIM AI features: most B2B
marketplace integrations and government/enterprise procurement systems require
these codes, and general-purpose PIM tools handle them poorly or not at all.

This file ships with a small illustrative lookup table for the demo category
(industrial controllers / PLCs). See STATUS_AND_ROADMAP.md item 5 for what a
real implementation needs (the full ETIM/ECLASS dictionaries are licensed data
sets — this is a scoped MVP, not a shortcut).
"""

from typing import Dict, Optional

CLASSIFICATION_TABLE = {
    "plc_controller": {
        "keywords": ["plc", "cpu", "simatic", "controller", "programmable logic"],
        "etim_class": "EC002542",
        "etim_class_name": "Modular PLC – CPU",
        "eclass_code": "27-37-16-01",
        "eclass_name": "Programmable logic controller",
        "unspsc": "43211900",
    },
    "temperature_sensor": {
        "keywords": ["temperature sensor", "thermocouple", "rtd", "thermometer"],
        "etim_class": "EC000891",
        "etim_class_name": "Temperature sensor",
        "eclass_code": "27-27-05-02",
        "eclass_name": "Temperature measuring instrument",
        "unspsc": "41113000",
    },
    "circuit_breaker": {
        "keywords": ["circuit breaker", "mcb", "mccb", "breaker"],
        "etim_class": "EC000042",
        "etim_class_name": "Miniature circuit breaker (MCB)",
        "eclass_code": "27-14-19-01",
        "eclass_name": "Miniature circuit breaker",
        "unspsc": "39121603",
    },
    "industrial_motor": {
        "keywords": ["motor", "ac motor", "induction motor", "drive"],
        "etim_class": "EC001851",
        "etim_class_name": "Electric motor",
        "eclass_code": "27-02-12-00",
        "eclass_name": "Electric motor",
        "unspsc": "26101100",
    },
}


def classify(product_name: str, product_description: str = "") -> Optional[Dict[str, str]]:
    text = f"{product_name} {product_description}".lower()
    for category, entry in CLASSIFICATION_TABLE.items():
        if any(kw in text for kw in entry["keywords"]):
            return {
                "category": category,
                "etim_class": entry["etim_class"],
                "etim_class_name": entry["etim_class_name"],
                "eclass_code": entry["eclass_code"],
                "eclass_name": entry["eclass_name"],
                "unspsc": entry["unspsc"],
            }
    return None
