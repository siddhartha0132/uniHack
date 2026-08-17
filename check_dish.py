import pandas as pd
df = pd.read_csv('data/raw/input_1000.csv')
dish = df[df['Part_Desc'].str.contains('Dishwasher', case=False, na=False)]
for _, row in dish.iterrows():
    print(f'{row["Mfg_Part_Num"]}: {row["Part_Desc"]}')