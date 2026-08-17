import pandas as pd
df = pd.read_csv('data/processed/output.csv')
abr = df[df['Mfg_Part_Num'].isin(['DCB518ASTS06G', '3MABR-7100075678', '49-94-0013', 'DBDS12125A01F'])]
for _, row in abr.iterrows():
    print(f'=== {row["Mfg_Part_Num"]} ===')
    print(f'  MANUFACTURER: {row.get("MANUFACTURER_NAME", "N/A")}')
    print(f'  BRAND: {row.get("BRAND_NAME", "N/A")}')
    print(f'  Classpath: {row.get("Classpath", "N/A")}')
    print(f'  INVOICE_DESC: {row.get("INVOICE_DESC", "N/A")}')
    print(f'  MOBILE_DESC: {row.get("MOBILE_DESC", "N/A")}')
    for i in range(1, 24):
        label = row.get(f'ATTRIBUTE_LABEL_{i}', '')
        val = row.get(f'ATTRIBUTE_VALUE_{i}', '')
        uom = row.get(f'ATTRIBUTE_UOM_{i}', '')
        if label and str(label).strip():
            print(f'  {label}: {val} {uom}')
    print()