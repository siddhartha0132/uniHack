"""
UOM Normalization — map any unit variant to approved abbreviation.
Based on Unilog_Master_UOM_Standards_Abbreviations_and_Terms.xlsx
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Tuple
import re

PROJECT_ROOT = Path(r"C:\Users\goels\uniHack")
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


class UOMNormalizer:
    def __init__(self):
        self.uom_map = {}  # variant -> approved
        self.measurement_types = {}  # approved -> measurement_type
        self._load_reference()
    
    def _load_reference(self):
        path = PROCESSED_DIR / "uom_standards.parquet"
        if not path.exists():
            # Build default map from common variants
            self._build_default_map()
            return
        
        df = pd.read_parquet(path)
        # Expected columns: MEASUREMENT_TYPE, APPROVED_ABBREVIATION, CAPTURE_FORM, EXAMPLE
        for _, row in df.iterrows():
            approved = str(row.get("APPROVED_ABBREVIATION", "")).strip()
            capture = str(row.get("CAPTURE_FORM", "")).strip()
            mtype = str(row.get("MEASUREMENT_TYPE", "")).strip()
            
            if approved:
                self.uom_map[approved.lower()] = approved
                self.measurement_types[approved] = mtype
            
            if capture and capture != approved:
                self.uom_map[capture.lower()] = approved
            
            # Add common variants
            variants = self._generate_variants(approved)
            for v in variants:
                self.uom_map[v.lower()] = approved
    
    def _build_default_map(self):
        """Fallback default UOM map when reference not available."""
        defaults = {
            # Length
            "in": "in", "inch": "in", "inches": "in", "\"": "in", "in.": "in",
            "ft": "ft", "foot": "ft", "feet": "ft", "'": "ft", "ft.": "ft",
            "yd": "yd", "yard": "yd",
            "mm": "mm", "millimeter": "mm", "millimeters": "mm",
            "cm": "cm", "centimeter": "cm",
            "m": "m", "meter": "m", "meters": "m",
            
            # Weight
            "lb": "lb", "lbs": "lb", "pound": "lb", "pounds": "lb", "#": "lb",
            "oz": "oz", "ounce": "oz", "ounces": "oz",
            "kg": "kg", "kilogram": "kg", "kilograms": "kg",
            "g": "g", "gram": "g", "grams": "g",
            "ton": "ton", "tons": "ton",
            
            # Volume
            "gal": "gal", "gallon": "gal", "gallons": "gal",
            "qt": "qt", "quart": "qt", "quarts": "qt",
            "pt": "pt", "pint": "pt", "pints": "pt",
            "fl oz": "fl oz", "fluid ounce": "fl oz",
            "ml": "ml", "milliliter": "ml",
            "l": "l", "liter": "l", "liters": "l",
            
            # Pressure
            "psi": "psi", "psig": "psig",
            "bar": "bar",
            "kpa": "kPa", "KPA": "kPa",
            
            # Temperature
            "f": "°F", "fahrenheit": "°F", "deg f": "°F",
            "c": "°C", "celsius": "°C", "deg c": "°C",
            
            # Electrical
            "v": "V", "volt": "V", "volts": "V",
            "a": "A", "amp": "A", "amps": "A", "ampere": "A",
            "w": "W", "watt": "W", "watts": "W",
            "hz": "Hz", "hertz": "Hz",
            "ohm": "Ω", "ohms": "Ω",
            
            # Count
            "ea": "ea", "each": "ea", "pc": "ea", "pcs": "ea", "piece": "ea", "pieces": "ea",
            "bx": "bx", "box": "bx", "boxes": "bx",
            "pk": "pk", "pack": "pk", "package": "pk",
            "ct": "ct", "count": "ct",
            
            # Area
            "sq in": "sq in", "sq ft": "sq ft", "sq yd": "sq yd",
            "sq mm": "sq mm", "sq cm": "sq cm", "sq m": "sq m",
            
            # Time
            "sec": "s", "second": "s", "seconds": "s",
            "min": "min", "minute": "min", "minutes": "min",
            "hr": "hr", "hour": "hr", "hours": "hr",
        }
        for variant, approved in defaults.items():
            self.uom_map[variant.lower()] = approved
    
    def _generate_variants(self, approved: str) -> list:
        """Generate common variants of an approved abbreviation."""
        variants = []
        # With/without periods
        if "." not in approved:
            variants.append(approved + ".")
        # Plural
        if not approved.endswith("s"):
            variants.append(approved + "s")
        # Case variants
        variants.extend([approved.upper(), approved.lower(), approved.capitalize()])
        return variants
    
    def normalize(self, raw_unit: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Normalize a raw unit string to approved abbreviation.
        Returns: (approved_abbreviation, measurement_type)
        """
        if not raw_unit or pd.isna(raw_unit):
            return None, None
        
        cleaned = str(raw_unit).strip().lower()
        # Remove common noise
        cleaned = re.sub(r'[^\w\s/°²³]', '', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Direct lookup
        if cleaned in self.uom_map:
            approved = self.uom_map[cleaned]
            return approved, self.measurement_types.get(approved)
        
        # Try partial match
        for variant, approved in self.uom_map.items():
            if variant in cleaned or cleaned in variant:
                return approved, self.measurement_types.get(approved)
        
        return raw_unit.strip(), None  # Return original if no match
    
    def format_value_unit(self, value: float, unit: str) -> str:
        """Format value with approved unit (space between number and unit)."""
        approved, _ = self.normalize(unit)
        if approved:
            return f"{value} {approved}"
        return f"{value} {unit}"


class DecimalFractionConverter:
    """Convert decimal inches to fractional inches (e.g., 50.25 -> 50-1/4)."""
    
    # Common industrial decimal thicknesses that should be preserved
    INDUSTRIAL_DECIMALS = {
        0.040, 0.045, 0.050, 0.060, 0.0625, 0.075, 0.090, 0.125, 
        0.156, 0.15625, 0.1875, 0.250, 0.3125, 0.375, 0.500
    }
    
    def __init__(self):
        self.decimal_to_fraction = {}
        self.fraction_to_decimal = {}
        self._load_reference()
    
    def _load_reference(self):
        path = PROCESSED_DIR / "decimal_fraction.parquet"
        if path.exists():
            df = pd.read_parquet(path)
            for _, row in df.iterrows():
                frac = str(row.get("fraction", "")).strip()
                dec = float(row.get("decimal", 0))
                self.decimal_to_fraction[dec] = frac
                self.fraction_to_decimal[frac] = dec
        else:
            # Standard 64ths
            for i in range(1, 64):
                dec = i / 64
                if i == 1:
                    frac = "1/64"
                elif i == 2:
                    frac = "1/32"
                elif i == 4:
                    frac = "1/16"
                elif i == 8:
                    frac = "1/8"
                elif i == 16:
                    frac = "1/4"
                elif i == 32:
                    frac = "1/2"
                elif i == 63:
                    frac = "63/64"
                else:
# Simplify fraction
                    from math import gcd
                    g = gcd(i, 64)
                    frac = f"{i//g}/{64//g}"
                self.decimal_to_fraction[round(dec, 6)] = frac
        
    def decimal_to_fraction_str(self, decimal_value: float) -> str:
        """Convert decimal inches to mixed fraction string (e.g., 50.25 -> 50-1/4).
        Preserves common industrial decimal thicknesses."""
        if decimal_value is None:
            return ""
        
        # Preserve common industrial decimal thicknesses
        if decimal_value in self.INDUSTRIAL_DECIMALS:
            return f"{decimal_value:.4f}".rstrip('0').rstrip('.')
        
        whole = int(decimal_value)
        frac_part = decimal_value - whole
        
        # Find closest 64th
        closest_64th = round(frac_part * 64) / 64
        
        if closest_64th == 0:
            return str(whole)
        elif closest_64th == 1:
            return str(whole + 1)
        
        frac_str = self.decimal_to_fraction.get(round(closest_64th, 6))
        if frac_str:
            if whole > 0:
                return f"{whole}-{frac_str}"
            return frac_str
        
        # Fallback
        return f"{decimal_value:.4f}".rstrip('0').rstrip('.')
    
    def parse_fraction_string(self, frac_str: str) -> float:
        """Parse fraction string (e.g., '50-1/4', '1/2', '3/4') to decimal."""
        if not frac_str:
            return 0.0
        
        frac_str = str(frac_str).strip()
        
        # Mixed fraction: 50-1/4
        if "-" in frac_str and "/" in frac_str:
            whole, frac = frac_str.split("-", 1)
            return float(whole) + self._parse_simple_fraction(frac)
        
        # Simple fraction: 1/2
        if "/" in frac_str:
            return self._parse_simple_fraction(frac_str)
        
        # Decimal
        try:
            return float(frac_str)
        except ValueError:
            return 0.0
    
    def _parse_simple_fraction(self, frac: str) -> float:
        parts = frac.split("/")
        if len(parts) == 2:
            try:
                return float(parts[0]) / float(parts[1])
            except (ValueError, ZeroDivisionError):
                pass
        return 0.0


# Global instances
uom_normalizer = UOMNormalizer()
decimal_fraction_converter = DecimalFractionConverter()


if __name__ == "__main__":
    # Test
    uom = UOMNormalizer()
    test_units = ["inches", "IN.", "inch", "ft", "feet", "mm", "lbs", "pounds", "psi", "deg F", "ea", "pcs"]
    for u in test_units:
        norm, mtype = uom.normalize(u)
        print(f"  {u:12} -> {norm:8} ({mtype})")
    
    dfc = DecimalFractionConverter()
    test_decimals = [0.5, 0.25, 0.75, 0.125, 0.015625, 50.25, 24.5, 1.0, 1.5]
    for d in test_decimals:
        print(f"  {d:8} -> {dfc.decimal_to_fraction_str(d)}")