import sys
sys.path.insert(0, 'src')
from extraction.lov_constrained_extractor import LOVConstraintEngine, CategoryClassifier

lov = LOVConstraintEngine()
clf = CategoryClassifier(lov)

test_cases = [
    ('PDSH4816AF Dishwasher SS - Display Only', 'Appliance Dealers Cooperative (APPDE)'),
    ('WDTS7024RZ Dishwasher SS - Display Only', 'Appliance Dealers Cooperative (APPDE)'),
    ('49-94-0013 Milw 5"x.045"x7/8" Metal Cut Off Disc', 'Milwaukee Accessory (4031)'),
    ('DCB518ASTS06G Diablo 1/2"x18" - Sanding Belt 6pc', 'Freud Inc (2435)'),
    ('543302126 6\' Wh Select T-Rail Kit Horiz - w/Sq Composite Balusters', 'U S Lumber (3073)'),
    ('25-A Charcoal Black 25-A Mortar - Type N', 'Rees Cast Stone Company (REECA)'),
]

for desc, mfr in test_cases:
    cp, conf = clf.classify(desc, mfr)
    print(f'{cp} (conf={conf:.2f}) <- {desc[:60]}')