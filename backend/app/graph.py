"""
graph.py
--------
Lightweight in-memory product relationship graph for the MVP demo.
Answers questions like "what's compatible with this part" and "what replaces it"
that flat attribute tables can't. In production this becomes a real graph database
(Neo4j) so it can scale past a hand-written dict and support graph queries —
see STATUS_AND_ROADMAP.md item 4.
"""

from typing import Dict, List

RELATIONSHIPS = {
    "6ES7214-1AG40-0XB0": {
        "manufacturer": "Siemens",
        "product_family": "SIMATIC S7-1200",
        "compatible_accessories": [
            {"id": "6ES7292-1AE30-0XA0", "name": "Signal board, analog input"},
            {"id": "6ES7231-4HD32-0XB0", "name": "Analog input module SM 1231"},
        ],
        "replacement_products": [],
        "related_family_members": [
            {"id": "6ES7212-1AE40-0XB0", "name": "CPU 1212C (smaller I/O count)"},
            {"id": "6ES7215-1AG40-0XB0", "name": "CPU 1215C (more I/O + 2 analog outputs)"},
        ],
    }
}


def get_related(product_id: str) -> Dict[str, List[dict]]:
    return RELATIONSHIPS.get(product_id, {
        "manufacturer": None,
        "product_family": None,
        "compatible_accessories": [],
        "replacement_products": [],
        "related_family_members": [],
    })
