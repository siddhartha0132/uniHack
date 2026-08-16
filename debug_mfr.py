import sys
sys.path.insert(0, 'src')
from normalization.mfr_brand_resolver import ManufacturerBrandResolver

resolver = ManufacturerBrandResolver()
test_cases = [
    'Freud Inc (2435)',
    'Milwaukee Accessory (4031)',
    '3 M Co (5293)',
]
for tc in test_cases:
    cleaned = resolver._clean_mfr_string(tc)
    print(f'{tc} -> cleaned: "{cleaned}"')
    match = resolver.resolve_manufacturer(tc, threshold=75)
    print(f'  match (thresh=75): {match}')
    match = resolver.resolve_manufacturer(tc, threshold=85)
    print(f'  match (thresh=85): {match}')