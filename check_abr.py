import pandas as pd
df = pd.read_csv('data/raw/input_1000.csv')
# Check abrasives
abr = df[df['Part_Desc'].str.contains('Cut.Off|Grinding|Sanding|Belt|Disc', case=False, na=False)]
for _, row in abr.head(20).iterrows():
    print(f'{row["Mfg_Part_Num"]}: {row["Part_Desc"]}')