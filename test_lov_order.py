import sys
sys.path.insert(0, 'src')
from extraction.lov_constrained_extractor import LOVConstraintEngine

lov = LOVConstraintEngine()
attrs = lov.get_attributes_for_classpath('Appliances & Consumer Electronics>Kitchen Appliances>Built-In Dishwashers')
for attr_name, attr_def in attrs.items():
    print(f'  {attr_name}: filterable={attr_def["filterable"]}')