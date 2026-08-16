import re

test_cases = [
    '49-94-0013 Milw 5"x.045"x7/8" Metal Cut Off Disc',
    '49-94-0029 Milw 6-1/2"x1/8"x5/8" DKO Metal Cut Off Disc',
    '49-94-0033 Milw 7"x1/16"x7/8" Metal Cut Off Disc',
    '49-94-0043 Milw 9"x3/32"x7/8" Metal Cut Off Disc',
    '49-94-0048 Milw 12"x7/64"x1" Metal Cut Off Disc General Purpose',
    'DBDS12125A01F Diablo 12"x1"x20mm Steel Demon Metal Cut-Off Disc',
    'DBDS14125G01F Diablo 14"x20mm Speed Demon Metal Cut-Off Disc',
    'DCB518ASTS06G Diablo 1/2"x18" Sanding Belt 6pc',
]

# Fixed compound pattern - handles:
# - diameter: integer or fraction (e.g., 5, 6-1/2, 12)
# - thickness: decimal starting with . or integer (e.g., .045, 1/8, 1)
# - arbor: fraction or integer + optional mm (e.g., 7/8, 5/8, 1, 20mm)
compound_pattern = r'(\d+(?:[./-]\d+)?)\s*[\"″]\s*x\s*(?:\.?\d+(?:\.\d+)?|\d+[./-]\d+)\s*[\"″]?\s*x\s*(\d+(?:[./-]\d+)?)\s*(?:[\"″]|mm)'

for desc in test_cases:
    compound = re.search(compound_pattern, desc)
    if compound:
        print(f'COMPOUND: {desc[:55]} -> {compound.groups()}')
    else:
        belt_pattern = r'(\d+(?:[./-]\d+)?)\s*[\"″]\s*x\s*(\d+(?:[./-]\d+)?)\s*[\"″]'
        belt = re.search(belt_pattern, desc)
        if belt:
            print(f'BELT: {desc[:55]} -> {belt.groups()}')
        else:
            print(f'NO MATCH: {desc[:55]}')

# Test simpler pattern
print("\n--- Testing simpler compound pattern ---")
simple_compound = r'(\d+(?:[./-]\d+)?)\s*[\"″]\s*x\s*([\d./-]+)\s*[\"″]?\s*x\s*(\d+(?:[./-]\d+)?)\s*(?:[\"″]|mm)'

for desc in test_cases:
    m = re.search(simple_compound, desc)
    if m:
        print(f'SIMPLE: {desc[:55]} -> {m.groups()}')
    else:
        print(f'SIMPLE NO: {desc[:55]}')