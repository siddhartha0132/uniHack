"""
Manufacturer/Brand Resolution using fuzzy matching against 27k approved list.
"""

import pandas as pd
from rapidfuzz import process, fuzz
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import re

PROJECT_ROOT = Path(__file__).parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


class ManufacturerBrandResolver:
    def __init__(self):
        self.mfr_df: pd.DataFrame = pd.DataFrame()
        self.brand_lookup: Dict[str, list[str]] = {}  # manufacturer_name -> list of brands
        self.all_manufacturers: list[str] = []
        self._load_reference()
    
    def _load_reference(self):
        path = PROCESSED_DIR / "manufacturer_brand.parquet"
        if not path.exists():
            print(f"WARNING: Manufacturer/Brand reference not found at {path}. Using empty resolver.")
            self.mfr_df = pd.DataFrame()
            self.brand_lookup = {}
            self.all_manufacturers = []
            return
        self.mfr_df = pd.read_parquet(path)
        # Build manufacturer -> brands mapping
        for _, row in self.mfr_df.iterrows():
            mfr = str(row.get("MANUFACTURER_NAME", "")).strip()
            brand = str(row.get("BRAND_NAME", "")).strip()
            if mfr and mfr != "nan":
                if mfr not in self.brand_lookup:
                    self.brand_lookup[mfr] = []
                if brand and brand != "nan":
                    self.brand_lookup[mfr].append(brand)
        # Also create flat list for fuzzy matching
        self.all_manufacturers = list(self.brand_lookup.keys())
    
    def resolve_manufacturer(self, raw_mfr: str, threshold: int = 85) -> Tuple[Optional[str], Optional[str], float]:
        """
        Resolve raw manufacturer string to canonical MANUFACTURER_NAME and CODE.
        Returns: (canonical_name, code, confidence_score)
        """
        if not raw_mfr or pd.isna(raw_mfr):
            return None, None, 0.0
        
        # If no reference data, return raw as-is with low confidence
        if self.mfr_df is None or self.mfr_df.empty or not self.all_manufacturers:
            return raw_mfr, None, 0.3
        
        # Clean input
        cleaned = self._clean_mfr_string(raw_mfr)
        
        # Direct match first
        exact = self.mfr_df[self.mfr_df["MANUFACTURER_NAME"].str.lower() == cleaned.lower()]
        if not exact.empty:
            row = exact.iloc[0]
            return row["MANUFACTURER_NAME"], row.get("MANUFACTURER_CODE"), 1.0
        
        # Fuzzy match
        match = process.extractOne(  # pyrefly: ignore[no-matching-overload]
            cleaned, 
            self.all_manufacturers, 
            scorer=fuzz.WRatio,
            score_cutoff=threshold
        )
        if match:
            canonical_name, score, _ = match
            row = self.mfr_df[self.mfr_df["MANUFACTURER_NAME"] == canonical_name].iloc[0]
            return canonical_name, row.get("MANUFACTURER_CODE"), score / 100.0
        
        return None, None, 0.0
    
    def resolve_brand(self, raw_brand: str, manufacturer: str, threshold: int = 85) -> Tuple[Optional[str], Optional[str], float]:
        """
        Resolve raw brand string to canonical BRAND_NAME and CODE for a given manufacturer.
        Returns: (canonical_brand_name, brand_code, confidence_score)
        """
        if not raw_brand or pd.isna(raw_brand):
            return None, None, 0.0
        
        # If no reference data, return raw as-is with low confidence
        if self.mfr_df is None or self.mfr_df.empty:
            return raw_brand, None, 0.3
        
        # If manufacturer resolved, check their brands first
        brands = self.brand_lookup.get(manufacturer, [])
        if brands:
            cleaned = self._clean_brand_string(raw_brand)
            match = process.extractOne(cleaned, brands, scorer=fuzz.WRatio, score_cutoff=threshold)  # pyrefly: ignore[no-matching-overload]
            if match:
                canonical_brand, score, _ = match
                row = self.mfr_df[
                    (self.mfr_df["MANUFACTURER_NAME"] == manufacturer) & 
                    (self.mfr_df["BRAND_NAME"] == canonical_brand)
                ]
                if not row.empty:
                    return canonical_brand, row.iloc[0].get("BRAND_CODE"), score / 100.0
        
        # Fallback: search all brands
        all_brands = self.mfr_df["BRAND_NAME"].dropna().unique().tolist()
        if all_brands:
            cleaned = self._clean_brand_string(raw_brand)
            match = process.extractOne(cleaned, all_brands, scorer=fuzz.WRatio, score_cutoff=threshold)  # pyrefly: ignore[no-matching-overload]
            if match:
                canonical_brand, score, _ = match
                row = self.mfr_df[self.mfr_df["BRAND_NAME"] == canonical_brand].iloc[0]
                return canonical_brand, row.get("BRAND_CODE"), score / 100.0
        
        return None, None, 0.0
    
    def _clean_mfr_string(self, s: str) -> str:
        """Remove parenthetical codes, Inc/LLC/Ltd suffixes for matching."""
        s = re.sub(r'\s*\([^)]+\)\s*', ' ', s)  # Remove (2435) codes
        s = re.sub(r'\b(Inc|LLC|Ltd|Corp|Corporation|Co|Company)\.?\b', '', s, flags=re.I)
        return re.sub(r'\s+', ' ', s).strip()
    
    def _clean_brand_string(self, s: str) -> str:
        # Strip symbols only for matching — canonical form preserves them
        s = re.sub(r'[®™©]', '', s)
        return re.sub(r'\s+', ' ', s).strip()
    
    def _get_canonical_brand_with_symbols(self, clean_brand: str, manufacturer: str) -> str:
        """Retrieve canonical brand name with ® / ™ symbols from the reference list."""
        if self.mfr_df is None or self.mfr_df.empty:
            return clean_brand
        # Look for exact match of stripped brand in the mfr list
        for _, row in self.mfr_df.iterrows():
            canonical = str(row.get('BRAND_NAME', '')).strip()
            stripped = re.sub(r'[®™©]', '', canonical).strip()
            if stripped.lower() == clean_brand.lower():
                return canonical
        return clean_brand


def resolve_row(row: pd.Series, resolver: ManufacturerBrandResolver) -> Dict[str, Any]:
    """Resolve manufacturer and brand for a single input row."""
    raw_mfr = row.get("Part_Manuf", "")
    raw_e1 = row.get("E1_Brand", "")
    raw_unilog = row.get("Unilog_Brand", "")
    raw_dib = row.get("DIB_Brand", "")
    part_desc = row.get("Part_Desc", "")
    
    # Resolve manufacturer from Part_Manuf
    canon_mfr, mfr_code, mfr_conf = resolver.resolve_manufacturer(raw_mfr)
    
    # Known distributors (not actual manufacturers) - deprioritize these
    known_distributors = {
        'appliance dealers cooperative',
        'jam industrial supply',
        'watsco', 'ferguson', 'hajoca', 'winwholesale',
        'home depot', 'lowes', 'menards', 'ace hardware',
        'grainger', 'mcmaster', 'fastenal', 'msc industrial',
        'u s lumber', 'boise cascade', 'parksite', 'park site',
        'v & v appliance parts', 'appliance dealers',
    }
    
    # Check if resolved manufacturer is a known distributor
    is_distributor = False
    if canon_mfr:
        mfr_lower = canon_mfr.lower()
        for dist in known_distributors:
            if dist in mfr_lower:
                is_distributor = True
                break
    
    # Also check raw manufacturer string for distributor names
    raw_mfr_lower = raw_mfr.lower()
    for dist in known_distributors:
        if dist in raw_mfr_lower:
            is_distributor = True
            break
    
    # Collect all brand hints from brand columns
    brand_hints = [b for b in [raw_e1, raw_unilog, raw_dib] if b and not pd.isna(b)]
    
    # Also extract brand hints from description
    desc_lower = part_desc.lower()
    
    # Appliance brands
    appliance_brands = {
        'frigidaire': ('Rheem Manufacturing', 'FRIGIDAIRE®'),
        'whirlpool': ('Whirlpool Corporation', 'Whirlpool®'),
        'kitchenaid': ('Whirlpool Corporation', 'KitchenAid®'),
        'kitchen aid': ('Whirlpool Corporation', 'KitchenAid®'),
        'ge ': ('GE Appliances', 'GE®'),
        'ge profile': ('GE Appliances', 'GE Profile®'),
        'monogram': ('GE Appliances', 'Monogram®'),
        'lg ': ('LG Electronics', 'LG®'),
        'lg signature': ('LG Electronics', 'LG Signature®'),
        'bosch': ('Bosch', 'Bosch®'),
        'samsung': ('Samsung', 'Samsung®'),
        'maytag': ('Whirlpool Corporation', 'Maytag®'),
        'amana': ('Whirlpool Corporation', 'Amana®'),
        'hotpoint': ('GE Appliances', 'Hotpoint®'),
    }
    
    # Abrasive/tool brands (extract from description)
    abrasive_brands = {
        'diablo': ('Freud Inc', 'Diablo'),
        'freud': ('Freud Inc', 'Freud'),
        'milw': ('Milwaukee Tool', 'Milwaukee'),
        'milwaukee': ('Milwaukee Tool', 'Milwaukee'),
        'cubitron': ('3M Company', 'Cubitron'),
        '3m': ('3M Company', '3M'),
        'scotch-brite': ('3M Company', 'Scotch-Brite'),
        'mirka': ('Mirka Abrasives Inc', 'Mirka'),
        'hiolit': ('Mirka Abrasives Inc', 'Hiolit'),
        'abranet': ('Mirka Abrasives Inc', 'Abranet'),
        'wera': ('Wera Tools', 'Wera'),
        'emseal': ('Emseal Joint Systems', 'Emseal'),
        'trex': ('Trex Company', 'Trex'),
        'timbertech': ('TimberTech', 'TimberTech'),
        'azek': ('TimberTech', 'AZEK'),
    }
    
    # MPN prefix to brand mapping (for dishwashers where brand not in description)
    mpn_prefix_brands = {
        'pdsh': ('Rheem Manufacturing', 'FRIGIDAIRE®'),
        'pdt': ('GE Appliances', 'GE®'),
        'ldph': ('LG Electronics', 'LG®'),
        'wdts': ('Whirlpool Corporation', 'Whirlpool®'),
        'pdd': ('GE Appliances', 'GE®'),
        'kdts': ('Whirlpool Corporation', 'KitchenAid®'),
        'kdps': ('Whirlpool Corporation', 'KitchenAid®'),
        'kdfm': ('Whirlpool Corporation', 'KitchenAid®'),
    }
    
    inferred_mfr = None
    inferred_brand = None
    
    # Check appliance brands first (from description)
    for brand_key, (mfr, brand) in appliance_brands.items():
        if brand_key in desc_lower:
            brand_hints.append(brand)
            inferred_mfr = mfr
            inferred_brand = brand
    
    # Check abrasive/tool brands (from description)
    for brand_key, (mfr, brand) in abrasive_brands.items():
        if brand_key in desc_lower:
            brand_hints.append(brand)
            inferred_mfr = mfr
            inferred_brand = brand
    
    # Check MPN prefix for dishwasher brands (when not in description)
    mfg_part_num = row.get("Mfg_Part_Num", "").lower()
    for prefix, (mfr, brand) in mpn_prefix_brands.items():
        if mfg_part_num.startswith(prefix):
            brand_hints.append(brand)
            inferred_mfr = mfr
            inferred_brand = brand
            break
    
    # If Part_Manuf is a known distributor AND we have a strong brand signal from description/MPN,
    # use the inferred manufacturer instead
    if is_distributor and inferred_mfr:
        canon_mfr, mfr_code, mfr_conf = inferred_mfr, None, 0.85
    elif is_distributor and not canon_mfr:
        # If distributor but no inference, keep distributor with low confidence
        mfr_conf = min(mfr_conf, 0.4)
    elif is_distributor and canon_mfr and canon_mfr in ['Appliance Dealers Cooperative']:
        # For known distributors without brand inference, lower confidence
        mfr_conf = min(mfr_conf, 0.5)
    
    # Resolve brand (use manufacturer context if available)
    canon_brand = None
    brand_code = None
    brand_conf = 0.0
    
    for hint in brand_hints:
        b_name, b_code, b_conf = resolver.resolve_brand(hint, canon_mfr or "")
        if b_conf > brand_conf:
            canon_brand, brand_code, brand_conf = b_name, b_code, b_conf
    
    # If we have an inferred_brand from the hardcoded map (which already has ® symbol),
    # prefer it if the fuzzy-matched brand is missing the ® or has lower confidence
    if inferred_brand:
        # Always use inferred_brand if it has a ® symbol that the fuzzy match lost
        import re as _re
        inferred_stripped = _re.sub(r'[®™©]', '', inferred_brand).strip()
        canon_stripped = _re.sub(r'[®™©]', '', canon_brand or '').strip()
        if inferred_stripped.lower() == canon_stripped.lower() and '\u00ae' in inferred_brand:
            # Same brand, but inferred has ® — use inferred
            canon_brand = inferred_brand
        elif not canon_brand:
            canon_brand = inferred_brand
            brand_conf = 0.75
            # Find brand code
            if canon_mfr and resolver.mfr_df is not None and not resolver.mfr_df.empty:
                brand_row = resolver.mfr_df[
                    (resolver.mfr_df["MANUFACTURER_NAME"] == canon_mfr) &
                    (resolver.mfr_df["BRAND_NAME"].str.replace(r'[®™©]', '', regex=True).str.strip() == inferred_stripped)
                ]
                if not brand_row.empty:
                    brand_code = brand_row.iloc[0].get("BRAND_CODE")
    
    # Don't default to first brand of manufacturer - only use explicit hints
    # (removed the fallback to first brand)
    
    return {
        "MANUFACTURER_NAME": canon_mfr,
        "MANUFACTURER_CODE": mfr_code,
        "BRAND_NAME": canon_brand,
        "BRAND_CODE": brand_code,
        "mfr_confidence": mfr_conf,
        "brand_confidence": brand_conf,
        "raw_manufacturer": raw_mfr,
        "raw_brands": brand_hints,
    }


if __name__ == "__main__":
    # Test with sample data
    resolver = ManufacturerBrandResolver()
    print(f"Loaded {len(resolver.all_manufacturers)} manufacturers")
    
    test_cases = [
        "Freud Inc (2435)",
        "Milwaukee Accessory (4031)", 
        "3 M Co (5293)",
        "Appliance Dealers Cooperative (APPDE)",
        "TIMBERTECH",
        "TREX",
    ]
    for tc in test_cases:
        name, code, conf = resolver.resolve_manufacturer(tc)
        print(f"  '{tc}' -> {name} ({code}) conf={conf:.2f}")