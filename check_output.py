import pandas as pd
df = pd.read_csv('data/processed/output.csv')
print('Mfg columns:', [c for c in df.columns if 'Mfg' in c])
dish = df[df.iloc[:, 11].isin(['PDSH4816AF', 'WDTS7024RZ'])]
for _, row in dish.iterrows():
    print(f'=== {row.iloc[11]} ===')
    print(f'  MANUFACTURER_NAME: {row.get("MANUFACTURER_NAME", "N/A")}')
    print(f'  BRAND_NAME: {row.get("BRAND_NAME", "N/A")}')
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