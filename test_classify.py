import sys
sys.path.insert(0, 'src')
from extraction.lov_constrained_extractor import LOVConstraintEngine, CategoryClassifier

lov = LOVConstraintEngine()
clf = CategoryClassifier(lov)

test_cases = [
    ('DBDS12125A01F Diablo 12"x1"x20mm Steel Demon Metal Cut-Off Disc', ''),
    ('DBDS14125G01F Diablo 14"x20mm Speed Demon Metal Cut-Off Disc', ''),
    ('49-94-0013 Milw 5"x.045"x7/8" Metal Cut Off Disc', ''),
]

for desc, mfr in test_cases:
    cp, conf = clf.classify(desc, mfr)
    print(f'{cp} (conf={conf:.2f}) <- {desc[:55]}')