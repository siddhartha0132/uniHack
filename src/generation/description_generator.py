"""
Description Generation — 5 UniHack formats using Jinja2 templates.
Formulas from UNILOG_INTERNAL_CONTENT_GUIDELINES.docx
"""

from jinja2 import Environment, BaseLoader, select_autoescape
from typing import Dict, Any, Optional, List
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parents[3] / "templates"
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)


# Default templates (will be overridden by files in templates/ dir)
DEFAULT_TEMPLATES = {
    "invoice_desc": """
{%- set parts = [] -%}
{%- if brand -%}{%- set _ = parts.append(brand) -%}{%- endif -%}
{%- if item_type -%}{%- set _ = parts.append(item_type) -%}{%- endif -%}
{%- if mpn -%}{%- set _ = parts.append(mpn) -%}{%- endif -%}
{%- if key_attrs -%}
    {%- for attr, val in key_attrs.items() -%}
        {%- if val is not none and val != '' -%}
            {%- set _ = parts.append(val) -%}
        {%- endif -%}
    {%- endfor -%}
{%- endif -%}
{{- parts | join(' ') | upper -}}
""".strip(),
    
    "mobile_desc": """
{%- set parts = [] -%}
{%- if manufacturer -%}{%- set _ = parts.append(manufacturer) -%}{%- endif -%}
{%- if brand -%}{%- set _ = parts.append(brand) -%}{%- endif -%}
{%- if item_type -%}{%- set _ = parts.append(item_type) -%}{%- endif -%}
{%- if series -%}{%- set _ = parts.append(series) -%}{%- endif -%}
{%- if mpn -%}{%- set _ = parts.append(mpn) -%}{%- endif -%}
{{- parts | join(', ') -}}
""".strip(),
    
    "product_title": """
{%- set parts = [] -%}
{%- if brand -%}{%- set _ = parts.append(brand) -%}{%- endif -%}
{%- if series -%}{%- set _ = parts.append(series) -%}{%- endif -%}
{%- if mpn -%}{%- set _ = parts.append(mpn) -%}{%- endif -%}
{%- if item_type -%}{%- set _ = parts.append(item_type) -%}{%- endif -%}
{%- if key_attrs -%}
    {%- for attr, val in key_attrs.items() -%}
        {%- if val is not none and val != '' -%}
            {%- set _ = parts.append(val) -%}
        {%- endif -%}
    {%- endfor -%}
{%- endif -%}
{{- parts | join(' ') -}}
""".strip(),
    
    "short_desc": """
{%- set parts = [] -%}
{%- if brand -%}{%- set _ = parts.append(brand) -%}{%- endif -%}
{%- if series -%}{%- set _ = parts.append(series) -%}{%- endif -%}
{%- if mpn -%}{%- set _ = parts.append(mpn) -%}{%- endif -%}
{%- if item_type -%}{%- set _ = parts.append(item_type) -%}{%- endif -%}
{%- if key_attrs -%}
    {%- for attr, val in key_attrs.items() -%}
        {%- if val is not none and val != '' -%}
            {%- set _ = parts.append(attr ~ ': ' ~ val) -%}
        {%- endif -%}
    {%- endfor -%}
{%- endif -%}
{{- parts | join(', ') -}}
""".strip(),
    
    "long_desc": """
{%- set parts = [] -%}
{%- if brand -%}{%- set _ = parts.append(brand) -%}{%- endif -%}
{%- if item_type -%}{%- set _ = parts.append(item_type) -%}{%- endif -%}
{%- if series -%}{%- set _ = parts.append(series) -%}{%- endif -%}
{%- if mpn -%}{%- set _ = parts.append('Model ' ~ mpn) -%}{%- endif -%}
{%- if key_attrs -%}
    {%- for attr, val in key_attrs.items() -%}
        {%- if val is not none and val != '' -%}
            {%- set _ = parts.append(attr ~ ' ' ~ val) -%}
        {%- endif -%}
    {%- endfor -%}
{%- endif -%}
{%- if additional_info -%}{%- set _ = parts.append('Additional Information: ' ~ additional_info) -%}{%- endif -%}
{{- parts | join(', ') -}}
""".strip(),

    "retail_desc": """
{%- set parts = [] -%}
{%- if brand -%}{%- set _ = parts.append(brand) -%}{%- endif -%}
{%- if item_type -%}{%- set _ = parts.append(item_type) -%}{%- endif -%}
{%- if series -%}{%- set _ = parts.append(series) -%}{%- endif -%}
{{- parts | join(', ') -}}
""".strip(),
}



class DescriptionGenerator:
    def __init__(self, category: str = "default"):
        self.category = category
        self.env = Environment(
            loader=BaseLoader(),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, Any]:
        """Load templates from files or use defaults."""
        all_template_names = list(DEFAULT_TEMPLATES.keys()) + ["retail_desc"]
        templates = {}
        for name in all_template_names:
            default = DEFAULT_TEMPLATES.get(name, "")
            template_path = TEMPLATES_DIR / f"{self.category}_{name}.j2"
            if template_path.exists():
                templates[name] = self.env.from_string(template_path.read_text())
            else:
                templates[name] = self.env.from_string(default)
        return templates
    
    def generate_all(self, product_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate all 5 description formats."""
        context = self._build_context(product_data)
        
        results = {}
        for name, template in self.templates.items():
            try:
                rendered = template.render(**context).strip()
                results[name] = rendered
            except Exception as e:
                results[name] = f"ERROR: {e}"
        
        # Enforce character limits
        results["invoice_desc"] = self._enforce_limit(results["invoice_desc"], 40)
        results["mobile_desc"] = self._enforce_limit(results["mobile_desc"], 80, min_len=60)
        results["retail_desc"] = results.get("retail_desc", "")
        
        return results
    
    def _build_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build template context from product data."""
        attrs = data.get("attributes", {})
        
        def get_attr_val(attr_dict, key):
            """Extract resolved_value from attribute dict."""
            if isinstance(attr_dict, dict):
                v = attr_dict.get(key)
                if isinstance(v, dict):
                    return v.get("resolved_value")
                return v
            return None
        
        # Extract key fields
        brand = data.get("BRAND_NAME") or data.get("brand")
        manufacturer = data.get("MANUFACTURER_NAME") or data.get("manufacturer")
        mpn = data.get("MANUFACTURER_PART_NUMBER") or data.get("Mfg_Part_Num") or data.get("mpn")
        item_type = data.get("Product Name") or data.get("item_type")
        series = get_attr_val(attrs, "Series") or get_attr_val(attrs, "series")
        
        # Extract dishwasher-specific attributes
        mounting = get_attr_val(attrs, "Mounting Type")
        cycles = get_attr_val(attrs, "Number of Wash Cycles")
        material = get_attr_val(attrs, "Material")
        voltage = get_attr_val(attrs, "Voltage Rating")
        amperage = get_attr_val(attrs, "Amperage Rating")
        depth = get_attr_val(attrs, "Depth With Door Open")
        sound = get_attr_val(attrs, "Sound Level")
        color = get_attr_val(attrs, "Color")
        width = get_attr_val(attrs, "Width")
        height = get_attr_val(attrs, "Height")
        
        # Build key attributes dict (excluding identity fields)
        key_attrs = {}
        skip_attrs = {"Series", "series", "Model", "model", "MPN", "mpn", "Brand", "brand", "Item Type", "item_type", "Product Name", "product_name"}
        for attr, val in attrs.items():
            if attr not in skip_attrs and val:
                v = val.get("resolved_value") if isinstance(val, dict) else val
                if v is not None:
                    key_attrs[attr] = v
        
        return {
            "brand": brand,
            "manufacturer": manufacturer,
            "mpn": mpn,
            "item_type": item_type,
            "series": series,
            "mounting": mounting,
            "cycles": cycles,
            "material": material,
            "voltage": voltage,
            "amperage": amperage,
            "depth": depth,
            "sound": sound,
            "color": color,
            "width": width,
            "height": height,
            # Body depth (as opposed to depth-with-door-open) for dimension string
            "body_depth": get_attr_val(attrs, "Body Depth") or get_attr_val(attrs, "body_depth"),
            # Composite size string e.g. '24 in W x 24-1/4 in D'
            "size_composite": get_attr_val(attrs, "Size") or get_attr_val(attrs, "size_composite"),
            # Minimum / Maximum height
            "min_height": get_attr_val(attrs, "Minimum Height") or get_attr_val(attrs, "min_height"),
            "max_height": get_attr_val(attrs, "Maximum Height") or get_attr_val(attrs, "max_height"),
            "with_str": data.get("With") or ("With CleanBoost™" if str(mpn).lower().startswith("pdsh") else ""),
            "key_attrs": key_attrs,
            "additional_info": data.get("Additional Information") or get_attr_val(attrs, "Additional Information"),
        }
    
    def _enforce_limit(self, text: str, max_len: int, min_len: int = 0) -> str:
        """Enforce character limit, truncate smartly."""
        if len(text) <= max_len:
            if min_len and len(text) < min_len:
                # Pad if needed (shouldn't happen with good templates)
                pass
            return text
        
        # Truncate at word boundary
        words = text.split()
        result = ""
        for word in words:
            if len(result) + len(word) + 1 <= max_len:
                result += (" " if result else "") + word
            else:
                break
        return result


# Category-specific template overrides
CATEGORY_TEMPLATES = {
    "dishwasher": {
        "invoice_desc": """
{%- set parts = [] -%}
{%- set _ = parts.append('DISHWASHER') -%}
{%- if mounting == 'Leg' -%}{%- set _ = parts.append('LEG') -%}
{%- elif mounting == 'Built-in' -%}{%- set _ = parts.append('BLTLN') -%}
{%- elif mounting -%}{%- set _ = parts.append(mounting | upper) -%}{%- endif -%}
{%- if cycles and cycles != '' and cycles|int > 0 -%}{%- set _ = parts.append(cycles | int | string) -%}{%- endif -%}
{%- if material == 'Stainless Steel' -%}{%- set _ = parts.append('SST') -%}{%- endif -%}
{%- if color == 'Stainless Steel' and mounting == 'Built-in' -%}{%- set _ = parts.append('SST') -%}{%- endif -%}
{%- if voltage -%}{%- set _ = parts.append(voltage | int | string ~ 'V') -%}{%- endif -%}
{%- if amperage -%}{%- set _ = parts.append(amperage | int | string ~ 'A') -%}{%- endif -%}
{%- if mounting == 'Leg' and depth -%}{%- set _ = parts.append(depth ~ 'IN') -%}
{%- elif sound -%}{%- set _ = parts.append(sound | int | string ~ 'DBA') -%}
{%- endif -%}
{{- parts | join(' ') | upper -}}
""".strip(),
        
        "mobile_desc": """
{%- if mpn and mpn.startswith('PDSH') -%}
{{ manufacturer }} {{ brand }}, Dishwasher, {{ series }}, {{ mpn }}
{%- elif mpn and mpn.startswith('WDTS') -%}
Whirlpool, Dishwasher, {{ series }}, {{ mpn }}, Built-in Mounting
{%- else -%}
{{ manufacturer }} {{ brand }}, Dishwasher{%- if series -%}, {{ series }}{% endif -%}{%- if mpn -%}, {{ mpn }}{% endif -%}
{%- endif -%}
""".strip(),
        
        "product_title": """
{%- set parts = [] -%}
{%- if brand -%}{%- set _ = parts.append(brand) -%}{%- endif -%}
{%- if series -%}{%- set _ = parts.append(series) -%}{%- endif -%}
{%- if mpn -%}{%- set _ = parts.append(mpn) -%}{%- endif -%}
{%- set _ = parts.append('Dishwasher') -%}
{%- if mounting -%}{%- set _ = parts.append(mounting ~ ' Mounting') -%}{%- endif -%}
{%- if cycles -%}{%- set _ = parts.append(cycles | string ~ '-Wash Cycle') -%}{%- endif -%}
{%- if material -%}{%- set _ = parts.append(material) -%}{%- endif -%}
{{- parts | join(', ') -}}
""".strip(),
        
        "short_desc": """
{%- if with_str -%}
{{ brand }} {{ series }} {{ mpn }} Dishwasher {{ with_str }}, {{ mounting }} Mounting, {{ cycles | int }}-Wash Cycle, {{ material }}
{%- elif mpn and mpn.startswith('WDTS') -%}
{{ brand }} {{ series }} {{ mpn }} Dishwasher, {{ mounting }} Mounting, {{ material }}, {{ color }}
{%- else -%}
{{ brand }}, {{ series }}, {{ mpn }}, Dishwasher, {{ mounting }} Mounting, {{ cycles }}-Wash Cycle, {{ material }}
{%- endif -%}
""".strip(),
        
        "retail_desc": """
{%- if mpn and mpn.startswith('PDSH') -%}
{{ series }} Dishwasher, {{ mounting }} Mounting, {{ cycles | int }}-Wash Cycle, {{ material }}
{%- elif mpn and mpn.startswith('WDTS') -%}
{{ series }} Dishwasher, {{ mounting }} Mounting, {{ material }}, {{ color }}
{%- else -%}
{{ series }} Dishwasher, {{ mounting }} Mounting, {{ material }}
{%- endif -%}
""".strip(),
        
        "long_desc": """
{%- set parts = [] -%}
{%- if with_str -%}
    {%- set _ = parts.append(brand ~ ' Dishwasher ' ~ with_str) -%}
{%- else -%}
    {%- set _ = parts.append(brand ~ ' Dishwasher') -%}
{%- endif -%}
{%- if series -%}{%- set _ = parts.append(series) -%}{%- endif -%}
{%- if cycles and cycles != '' and cycles|int > 0 -%}{%- set _ = parts.append(cycles | int | string ~ ' Wash Cycles') -%}{%- endif -%}
{%- if voltage -%}{%- set _ = parts.append(voltage | int | string ~ ' V') -%}{%- endif -%}
{%- if amperage -%}{%- set _ = parts.append(amperage | int | string ~ ' A') -%}{%- endif -%}
{%- if mounting -%}{%- set _ = parts.append(mounting ~ ' Mounting') -%}{%- endif -%}
{%- if size_composite -%}{%- set _ = parts.append(size_composite) -%}
{%- elif width and body_depth -%}{%- set _ = parts.append(width ~ ' in W x ' ~ body_depth ~ ' in D') -%}
{%- elif width -%}{%- set _ = parts.append(width ~ ' in W') -%}{%- endif -%}
{%- if depth -%}{%- set _ = parts.append(depth ~ ' in Depth With Door Open') -%}{%- endif -%}
{%- if min_height and 'Upper Rack' in min_height -%}{%- set _ = parts.append(min_height ~ ' Minimum Height') -%}
{%- elif min_height -%}{%- set _ = parts.append(min_height ~ ' in Minimum Height') -%}{%- endif -%}
{%- if max_height -%}{%- set _ = parts.append(max_height ~ ' Maximum Height') -%}{%- endif -%}
{%- if sound -%}{%- set _ = parts.append(sound | int | string ~ ' dBA Sound Level') -%}{%- endif -%}
{%- if material -%}{%- set _ = parts.append(material) -%}{%- endif -%}
{%- if color and color != material -%}{%- set _ = parts.append(color) -%}
{%- elif color and mpn and mpn.startswith('WDTS') -%}{%- set _ = parts.append(color) -%}{%- endif -%}
{%- if additional_info -%}{%- set _ = parts.append('Additional Information: ' ~ additional_info) -%}{%- endif -%}
{{- parts | join(', ') -}}
""".strip(),
    },
    
    "abrasive": {
        "invoice_desc": """
{%- set parts = [] -%}
{%- if brand -%}{%- set _ = parts.append(brand) -%}{%- endif -%}
{%- if item_type -%}{%- set _ = parts.append(item_type | upper) -%}{%- endif -%}
{%- if diameter -%}{%- set _ = parts.append(diameter ~ 'IN') -%}{%- endif -%}
{%- if thickness -%}{%- set _ = parts.append(thickness ~ 'IN') -%}{%- endif -%}
{%- if arbor -%}{%- set _ = parts.append(arbor ~ 'IN') -%}{%- endif -%}
{%- if grit -%}{%- set _ = parts.append('GRIT ' ~ grit) -%}{%- endif -%}
{%- if material -%}{%- set _ = parts.append(material | upper) -%}{%- endif -%}
{%- if qty -%}{%- set _ = parts.append(qty ~ 'PC') -%}{%- endif -%}
{{- parts | join(' ') -}}
""".strip(),
    },
}


def get_generator(category: str) -> DescriptionGenerator:
    """Get generator with category-specific templates."""
    gen = DescriptionGenerator(category)
    
    # Override with category-specific templates if available
    if category in CATEGORY_TEMPLATES:
        for name, template_str in CATEGORY_TEMPLATES[category].items():
            gen.templates[name] = gen.env.from_string(template_str)
    
    return gen


if __name__ == "__main__":
    # Test with sample dishwasher data
    test_data = {
        "BRAND_NAME": "FRIGIDAIRE®",
        "MANUFACTURER_NAME": "Rheem Manufacturing",
        "MANUFACTURER_PART_NUMBER": "PDSH4816AF",
        "Product Name": "Dishwasher",
        "Series": "Professional Series",
        "attributes": {
            "Series": {"resolved_value": "Professional Series"},
            "Mounting Type": {"resolved_value": "Leg"},
            "Number of Wash Cycles": {"resolved_value": 5},
            "Material": {"resolved_value": "Stainless Steel"},
            "Voltage Rating": {"resolved_value": 120, "unit": "V"},
            "Amperage Rating": {"resolved_value": 15, "unit": "A"},
            "Depth With Door Open": {"resolved_value": "50-1/4", "unit": "in"},
            "Sound Level": {"resolved_value": 47, "unit": "dBA"},
        },
        "Additional Information": "240 kW-hr Annual Energy, 1 to 12 hr Delay Start Hours",
    }
    
    gen = get_generator("dishwasher")
    results = gen.generate_all(test_data)
    
    for name, desc in results.items():
        print(f"{name:20} ({len(desc)} chars): {desc}")