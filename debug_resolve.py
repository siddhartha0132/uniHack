import sys
sys.path.insert(0, 'src')
from normalization.mfr_brand_resolver import ManufacturerBrandResolver, resolve_row
import pandas as pd

# Load test rows
df = pd.read_csv('data/raw/input_1000.csv')

# Test PDSH4816AF
row = df[df['Mfg_Part_Num'] == 'PDSH4816AF'].iloc[0]
print(f"Part_Desc: {row['Part_Desc']}")
print(f"Part_Manuf: {row['Part_Manuf']}")
print(f"E1_Brand: {row['E1_Brand']}")
print(f"Unilog_Brand: {row['Unilog_Brand']}")
print(f"DIB_Brand: {row['DIB_Brand']}")

resolver = ManufacturerBrandResolver()
result = resolve_row(row, resolver)
print(f"\nResult: {result}")

# Test WDTS7024RZ
row2 = df[df['Mfg_Part_Num'] == 'WDTS7024RZ'].iloc[0]
print(f"\n\nPart_Desc: {row2['Part_Desc']}")
print(f"Part_Manuf: {row2['Part_Manuf']}")
result2 = resolve_row(row2, resolver)
print(f"Result: {result2}")

# Test 3M abrasive
row3 = df[df['Mfg_Part_Num'] == '3MABR-7100075678'].iloc[0]
print(f"\n\nPart_Desc: {row3['Part_Desc']}")
print(f"Part_Manuf: {row3['Part_Manuf']}")
result3 = resolve_row(row3, resolver)
print(f"Result: {result3}")

# Test Freud
row4 = df[df['Mfg_Part_Num'] == 'DCB518ASTS06G'].iloc[0]
print(f"\n\nPart_Desc: {row4['Part_Desc']}")
print(f"Part_Manuf: {row4['Part_Manuf']}")
result4 = resolve_row(row4, resolver)
print(f"Result: {result4}")

# Test Milwaukee
row5 = df[df['Mfg_Part_Num'] == '49-94-0013'].iloc[0]
print(f"\n\nPart_Desc: {row5['Part_Desc']}")
print(f"Part_Manuf: {row5['Part_Manuf']}")
result5 = resolve_row(row5, resolver)
print(f"Result: {result5}")