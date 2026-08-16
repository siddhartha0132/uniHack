import re

test_cases = [
    'DBDS12125A01F Diablo 12"x1"x20mm Steel Demon Metal Cut-Off Disc',
    'DBDS14125G01F Diablo 14"x20mm Speed Demon Metal Cut-Off Disc',
    '49-94-0013 Milw 5"x.045"x7/8" Metal Cut Off Disc',
]

compound_pattern = r'(\d+(?:[./-]\d+)?)\s*[\"″]\s*x\s*([\d./-]+)\s*[\"″]?\s*x\s*(\d+(?:[./-]\d+)?)\s*(?:[\"″]|mm)'

for desc in test_cases:
    m = re.search(compound_pattern, desc)
    print(f'{desc[:50]} -> {m.groups() if m else None}')