import pandas as pd
from pathlib import Path

raw = Path('data/raw')

# Update manufacturer list with more aliases
mfr_data = [
    {'MANUFACTURER_NAME': 'Freud Inc', 'MANUFACTURER_CODE': '2435', 'BRAND_NAME': 'Diablo', 'BRAND_CODE': 'DIAB'},
    {'MANUFACTURER_NAME': 'Freud Inc', 'MANUFACTURER_CODE': '2435', 'BRAND_NAME': 'Freud', 'BRAND_CODE': 'FREU'},
    {'MANUFACTURER_NAME': 'Milwaukee Tool', 'MANUFACTURER_CODE': '4031', 'BRAND_NAME': 'Milwaukee', 'BRAND_CODE': 'MILW'},
    {'MANUFACTURER_NAME': 'Milwaukee Tool', 'MANUFACTURER_CODE': '4031', 'BRAND_NAME': 'MILWAUKEE', 'BRAND_CODE': 'MILW'},
    {'MANUFACTURER_NAME': 'Milwaukee Accessory', 'MANUFACTURER_CODE': '4031', 'BRAND_NAME': 'Milwaukee', 'BRAND_CODE': 'MILW'},  # Alias
    {'MANUFACTURER_NAME': '3M Company', 'MANUFACTURER_CODE': '5293', 'BRAND_NAME': '3M', 'BRAND_CODE': '3M'},
    {'MANUFACTURER_NAME': '3M Company', 'MANUFACTURER_CODE': '5293', 'BRAND_NAME': 'Cubitron', 'BRAND_CODE': 'CUB'},
    {'MANUFACTURER_NAME': '3M', 'MANUFACTURER_CODE': '5293', 'BRAND_NAME': '3M', 'BRAND_CODE': '3M'},  # Alias
    {'MANUFACTURER_NAME': '3 M Co', 'MANUFACTURER_CODE': '5293', 'BRAND_NAME': '3M', 'BRAND_CODE': '3M'},  # Alias
    {'MANUFACTURER_NAME': 'Mirka Abrasives Inc', 'MANUFACTURER_CODE': 'MIRUS', 'BRAND_NAME': 'Mirka', 'BRAND_CODE': 'MIRK'},
    {'MANUFACTURER_NAME': 'Mirka Abrasives Inc', 'MANUFACTURER_CODE': 'MIRUS', 'BRAND_NAME': 'Hiolit', 'BRAND_CODE': 'HIOL'},
    {'MANUFACTURER_NAME': 'Mirka Abrasives Inc', 'MANUFACTURER_CODE': 'MIRUS', 'BRAND_NAME': 'Abranet', 'BRAND_CODE': 'ABRA'},
    {'MANUFACTURER_NAME': 'Rheem Manufacturing', 'MANUFACTURER_CODE': 'RHEEM', 'BRAND_NAME': 'FRIGIDAIRE', 'BRAND_CODE': 'FRIG'},
    {'MANUFACTURER_NAME': 'Whirlpool Corporation', 'MANUFACTURER_CODE': 'WHIRL', 'BRAND_NAME': 'Whirlpool', 'BRAND_CODE': 'WHIR'},
    {'MANUFACTURER_NAME': 'Whirlpool Corporation', 'MANUFACTURER_CODE': 'WHIRL', 'BRAND_NAME': 'KitchenAid', 'BRAND_CODE': 'KITCH'},
    {'MANUFACTURER_NAME': 'LG Electronics', 'MANUFACTURER_CODE': 'LG', 'BRAND_NAME': 'LG', 'BRAND_CODE': 'LG'},
    {'MANUFACTURER_NAME': 'GE Appliances', 'MANUFACTURER_CODE': 'GE', 'BRAND_NAME': 'GE', 'BRAND_CODE': 'GE'},
    {'MANUFACTURER_NAME': 'GE Appliances', 'MANUFACTURER_CODE': 'GE', 'BRAND_NAME': 'GE Profile', 'BRAND_CODE': 'GEPR'},
    {'MANUFACTURER_NAME': 'Bosch', 'MANUFACTURER_CODE': 'BOSCH', 'BRAND_NAME': 'Bosch', 'BRAND_CODE': 'BOSCH'},
    {'MANUFACTURER_NAME': 'Samsung', 'MANUFACTURER_CODE': 'SAMS', 'BRAND_NAME': 'Samsung', 'BRAND_CODE': 'SAMS'},
    {'MANUFACTURER_NAME': 'TimberTech', 'MANUFACTURER_CODE': 'TIMB', 'BRAND_NAME': 'TimberTech', 'BRAND_CODE': 'TIMB'},
    {'MANUFACTURER_NAME': 'TimberTech', 'MANUFACTURER_CODE': 'TIMB', 'BRAND_NAME': 'AZEK', 'BRAND_CODE': 'AZEK'},
    {'MANUFACTURER_NAME': 'Trex Company', 'MANUFACTURER_CODE': 'TREX', 'BRAND_NAME': 'Trex', 'BRAND_CODE': 'TREX'},
    {'MANUFACTURER_NAME': 'Wera Tools', 'MANUFACTURER_CODE': 'WERA', 'BRAND_NAME': 'Wera', 'BRAND_CODE': 'WERA'},
    {'MANUFACTURER_NAME': 'Emseal Joint Systems', 'MANUFACTURER_CODE': 'EMSE', 'BRAND_NAME': 'Emseal', 'BRAND_CODE': 'EMSE'},
    {'MANUFACTURER_NAME': 'Rees Cast Stone', 'MANUFACTURER_CODE': 'REES', 'BRAND_NAME': 'Rees', 'BRAND_CODE': 'REES'},
    {'MANUFACTURER_NAME': 'US Lumber', 'MANUFACTURER_CODE': 'USLUM', 'BRAND_NAME': 'US Lumber', 'BRAND_CODE': 'USLUM'},
    {'MANUFACTURER_NAME': 'Boise Cascade', 'MANUFACTURER_CODE': 'BOICA', 'BRAND_NAME': 'Boise Cascade', 'BRAND_CODE': 'BOICA'},
    {'MANUFACTURER_NAME': 'Parksite', 'MANUFACTURER_CODE': 'PARK', 'BRAND_NAME': 'Parksite', 'BRAND_CODE': 'PARK'},
    # Distributors (for reference)
    {'MANUFACTURER_NAME': 'Appliance Dealers Cooperative', 'MANUFACTURER_CODE': 'APPDE', 'BRAND_NAME': 'FRIGIDAIRE', 'BRAND_CODE': 'FRIG'},
    {'MANUFACTURER_NAME': 'Appliance Dealers Cooperative', 'MANUFACTURER_CODE': 'APPDE', 'BRAND_NAME': 'Whirlpool', 'BRAND_CODE': 'WHIR'},
    {'MANUFACTURER_NAME': 'Appliance Dealers Cooperative', 'MANUFACTURER_CODE': 'APPDE', 'BRAND_NAME': 'LG', 'BRAND_CODE': 'LG'},
    {'MANUFACTURER_NAME': 'Appliance Dealers Cooperative', 'MANUFACTURER_CODE': 'APPDE', 'BRAND_NAME': 'GE', 'BRAND_CODE': 'GE'},
    {'MANUFACTURER_NAME': 'Appliance Dealers Cooperative', 'MANUFACTURER_CODE': 'APPDE', 'BRAND_NAME': 'KitchenAid', 'BRAND_CODE': 'KITCH'},
]

pd.DataFrame(mfr_data).to_excel(raw / 'UniCat_Manufacturer_and_Brand_List.xlsx', index=False)
print('Updated manufacturer list with aliases')

# Re-run ingestion
import subprocess
result = subprocess.run(['py', 'src/ingestion/load_reference_files.py'], capture_output=True, text=True)
print(result.stdout)
print(result.stderr)