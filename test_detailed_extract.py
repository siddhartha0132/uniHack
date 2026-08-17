import sys
sys.path.insert(0, 'src')
from pipeline import UniHackPipeline

pipeline = UniHackPipeline()

# Test DBDS12125A01F
import pandas as pd
df = pd.read_csv('data/raw/input_1000.csv')
row = df[df['Mfg_Part_Num'] == 'DBDS12125A01F'].iloc[0]
print(f"Part_Desc: {row['Part_Desc']}")
print(f"Part_Manuf: {row['Part_Manuf']}")

# Test classification
part_desc = row.get("Part_Desc", "")
part_manuf = row.get("Part_Manuf", "")
classpath, class_conf = pipeline.classifier.classify(part_desc, part_manuf)
print(f"Classpath: {classpath} (conf={class_conf})")

# Test detailed extraction
attrs = pipeline._extract_abrasive_attrs_detailed(part_desc)
print(f"Detailed attrs: {attrs}")

# Test basic extraction
basic = pipeline._extract_abrasive_attrs(part_desc)
print(f"Basic attrs: {basic}")

# Test full extraction
full = pipeline._extract_attributes(part_desc, classpath)
print(f"Full attrs: {full}")