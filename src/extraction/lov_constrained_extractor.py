"""
LOV-Constrained Attribute Extraction
Uses Unicat_Lov to validate and normalize extracted attribute values.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from rapidfuzz import process, fuzz
import re

PROJECT_ROOT = Path(__file__).parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


class LOVConstraintEngine:
    def __init__(self):
        self.lov_df = None
        self.classpath_attributes = {}  # classpath -> list of attribute configs
        self.value_normalizers = {}  # (classpath, attribute) -> normalizer function
        self._load_reference()
    
    def _load_reference(self):
        path = PROCESSED_DIR / "lov.parquet"
        if not path.exists():
            print("WARNING: LOV not loaded. Run ingestion first.")
            return
        
        self.lov_df = pd.read_parquet(path)
        # Expected columns: Classpath, Leaf Node, Filtering Y/N, Attribute Label, 
        # Attribute Values, Normalized Label, Normalized Values, Guidelines, Remarks
        
        self._build_classpath_index()
    
    def _build_classpath_index(self):
        """Build index of attributes per classpath with allowed values."""
        if self.lov_df is None:
            return
        for _, row in self.lov_df.iterrows():
            classpath = str(row.get("Classpath", "")).strip()
            attr_label = str(row.get("Attribute Label", "")).strip()
            normalized_label = str(row.get("Normalized Label", "")).strip()
            attr_values = str(row.get("Attribute Values", "")).strip()
            normalized_values = str(row.get("Normalized Values", "")).strip()
            filtering = str(row.get("Filtering Y/N", "")).strip()
            leaf_node = str(row.get("Leaf Node", "")).strip()
            guidelines = str(row.get("Guidelines", "")).strip()
            
            if not classpath or not attr_label:
                continue
            
            # Use normalized label if available, else original
            key_attr = normalized_label if normalized_label and normalized_values != "nan" else attr_label
            
            # Parse allowed values (comma/semicolon/pipe separated)
            allowed_values = self._parse_values(normalized_values if normalized_values != "nan" else attr_values)
            
            if classpath not in self.classpath_attributes:
                self.classpath_attributes[classpath] = {}
            
            self.classpath_attributes[classpath][key_attr] = {
                "original_label": attr_label,
                "normalized_label": normalized_label,
                "allowed_values": allowed_values,
                "filterable": filtering.upper() == "Y",
                "leaf_node": leaf_node,
                "guidelines": guidelines,
            }
            
            # Build value normalizer for this attribute
            if allowed_values:
                self.value_normalizers[(classpath, key_attr)] = self._make_normalizer(allowed_values)
    
    def _parse_values(self, val_str: str) -> List[str]:
        """Parse comma/semicolon/pipe separated values."""
        if not val_str or val_str == "nan":
            return []
        # Split on common delimiters
        parts = re.split(r'[;,|]', val_str)
        return [p.strip() for p in parts if p.strip()]
    
    def _make_normalizer(self, allowed_values: List[str]):
        """Create a function that normalizes any value to closest allowed value."""
        def normalize(value: str) -> Tuple[Optional[str], float]:
            if not value:
                return None, 0.0
            # Direct match
            for av in allowed_values:
                if value.strip().lower() == av.strip().lower():
                    return av, 1.0
            # Fuzzy match
            match = process.extractOne(value.strip(), allowed_values, scorer=fuzz.WRatio, score_cutoff=80)  # pyrefly: ignore[no-matching-overload]
            if match:
                return match[0], match[1] / 100.0
            return None, 0.0
        return normalize
    
    def get_attributes_for_classpath(self, classpath: str) -> Dict[str, Dict]:
        """Get all attribute definitions for a classpath."""
        # Try exact match first
        if classpath in self.classpath_attributes:
            return self.classpath_attributes[classpath]
        
        # Try prefix match (e.g., "Appliances & Consumer Electronics>Kitchen Appliances>Built-In Dishwashers")
        for cp in self.classpath_attributes:
            if classpath.startswith(cp) or cp.startswith(classpath):
                return self.classpath_attributes[cp]
        
        return {}
    
    def normalize_value(self, classpath: str, attribute: str, value: str) -> Tuple[Optional[str], float]:
        """Normalize a value to LOV-allowed value for given classpath/attribute."""
        key = (classpath, attribute)
        if key in self.value_normalizers:
            return self.value_normalizers[key](value)
        
        # Try with normalized attribute name
        attrs = self.get_attributes_for_classpath(classpath)
        for attr_key, attr_def in attrs.items():
            if attr_key.lower() == attribute.lower():
                allowed = attr_def["allowed_values"]
                if allowed:
                    match = process.extractOne(value.strip(), allowed, scorer=fuzz.WRatio, score_cutoff=80)  # pyrefly: ignore[no-matching-overload]
                    if match:
                        return match[0], match[1] / 100.0
        
        return value, 0.5  # No constraint, medium confidence
    
    def validate_extraction(self, classpath: str, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize all extracted attributes against LOV."""
        validated = {}
        attr_defs = self.get_attributes_for_classpath(classpath)
        
        for attr_name, attr_data in attributes.items():
            # Find matching LOV attribute
            lov_attr = None
            for lov_key in attr_defs:
                if lov_key.lower() == attr_name.lower() or attr_name.lower() in lov_key.lower():
                    lov_attr = lov_key
                    break
            
            if lov_attr:
                allowed = attr_defs[lov_attr]["allowed_values"]
                if allowed:
                    raw_value = attr_data.get("value") or attr_data.get("resolved_value")
                    normalized, conf = self.normalize_value(classpath, lov_attr, str(raw_value))
                    validated[lov_attr] = {
                        **attr_data,
                        "value": normalized,
                        "lov_confidence": conf,
                        "lov_validated": normalized is not None,
                        "original_value": raw_value,
                    }
                else:
                    validated[lov_attr] = {**attr_data, "lov_confidence": 1.0, "lov_validated": True}
            else:
                # Attribute not in LOV for this classpath
                validated[attr_name] = {**attr_data, "lov_confidence": 0.0, "lov_validated": False, "lov_note": "Not in LOV for classpath"}
        
        # Check for missing required (filterable) attributes
        for lov_key, attr_def in attr_defs.items():
            if attr_def["filterable"] and lov_key not in validated:
                validated[lov_key] = {
                    "value": None,
                    "status": "missing_required",
                    "lov_confidence": 0.0,
                    "lov_validated": False,
                    "lov_note": f"Required (filterable) attribute missing for {classpath}",
                }
        
        return validated


class CategoryClassifier:
    """Classify Part_Desc to classpath using keyword rules + ML."""
    
    def __init__(self, lov_engine: LOVConstraintEngine):
        self.lov_engine = lov_engine
        self.classpaths = list(lov_engine.classpath_attributes.keys())
        self._build_keyword_rules()
    
    def _build_keyword_rules(self):
        """Build keyword-based classification rules from LOV leaf nodes and product terms."""
        self.keyword_rules = {}
        
        # Manual keyword mapping for better classification
        classpath_keywords = {
            'Appliances & Consumer Electronics>Kitchen Appliances>Built-In Dishwashers': 
                ['dishwasher', 'dish wash', 'built-in', 'builtin', 'kitchen appliance'],
            'Tools & Workshop Equipment>Abrasives>Cut-Off Wheels': 
                ['cut.off', 'cut off', 'cutoff', 'cut-off disc', 'cut off wheel', 'metal cut', 'masonry cut', 'cut-off wheel'],
            'Tools & Workshop Equipment>Abrasives>Grinding Wheels': 
                ['grinding wheel', 'grinding disc', 'metal grinding', 'masonry grinding'],
            'Tools & Workshop Equipment>Abrasives>Sanding Belts': 
                ['sanding belt', 'sanding disc', 'sanding sponge', 'abrasive belt', 'stikit', 'film', 'disc', 'cubitron', 'hook and loop', 'psa', 'pressure sensitive adhesive'],
            'Building Materials>Decking & Railing>Composite Decking': 
                ['decking', 'rail kit', 'railing', 'baluster', 'composite deck', 't-rail', 'finyline'],
            'Building Materials>Masonry>Mortar': 
                ['mortar', 'type n', 'type s', 'type m'],
        }
        
        for cp, attrs in self.lov_engine.classpath_attributes.items():
            keywords = classpath_keywords.get(cp, [])
            
            # Add leaf node words
            leaf_nodes = set()
            for attr_def in attrs.values():
                if attr_def["leaf_node"]:
                    leaf_nodes.add(attr_def["leaf_node"].lower())
            for ln in leaf_nodes:
                keywords.extend(ln.split())
            
            # Add attribute label words (Series, Mounting, etc.)
            for attr_label in attrs.keys():
                keywords.extend(attr_label.lower().split())
            
            self.keyword_rules[cp] = list(set(keywords))
    
    def classify(self, part_desc: str, part_manuf: str = "") -> Tuple[str, float]:
        """Classify description to classpath. Returns (classpath, confidence)."""
        if not part_desc:
            return "", 0.0
        
        text = (part_desc + " " + part_manuf).lower()
        
        best_cp = ""
        best_score = 0
        
        for cp, keywords in self.keyword_rules.items():
            # Count keyword matches
            matches = sum(1 for kw in keywords if kw in text)
            if matches > 0:
                # Score based on number of matches, boosted for specific terms
                score = matches * 2
                # Extra boost for leaf node exact match
                for attr_def in self.lov_engine.classpath_attributes[cp].values():
                    leaf = attr_def["leaf_node"].lower()
                    if leaf and leaf in text:
                        score += 5
                if score > best_score:
                    best_score = score
                    best_cp = cp
        
        # Also check manufacturer for appliance brands
        if not best_cp and 'appliance' in text:
            best_cp = 'Appliances & Consumer Electronics>Kitchen Appliances>Built-In Dishwashers'
            best_score = 1
        
        return best_cp, min(best_score / 10, 1.0)


if __name__ == "__main__":
    # Test when LOV is available
    try:
        lov = LOVConstraintEngine()
        print(f"Loaded LOV with {len(lov.classpath_attributes)} classpaths")
        for cp in list(lov.classpath_attributes.keys())[:5]:
            attrs = lov.classpath_attributes[cp]
            print(f"  {cp}: {len(attrs)} attributes")
            for attr, defn in list(attrs.items())[:3]:
                print(f"    {attr}: {len(defn['allowed_values'])} values, filterable={defn['filterable']}")
    except Exception as e:
        print(f"LOV not available: {e}")