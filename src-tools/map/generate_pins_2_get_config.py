#!/usr/bin/env python
import os
import json

if __name__ == '__main__':
    current_dir = os.path.dirname(__file__)
    root_path = os.path.join(current_dir, '..', '..', 'src', 'rogerthat', 'bizz', 'maps', 'services', 'places')
    
    verticals_path = os.path.join(root_path, 'verticals.json')
    with open(verticals_path, 'r') as f:
        verticals_data = json.load(f)
    
    classification_path = os.path.join(root_path, 'classification.json')
    with open(classification_path, 'r') as f:
        classifications_data = json.load(f)
        
    categories_path = os.path.join(root_path, 'categories.json')
    with open(categories_path, 'r') as f:
        categories_data = json.load(f)
        
    icons_to_generate = set()
    
    for v in verticals_data.itervalues():
        icons_to_generate.add("%s%s" % (v['icon'], v['color']))
        
    for place_type, v in categories_data.iteritems():
        for vertical, place_types in classifications_data.iteritems():
            if place_type in place_types:
                icons_to_generate.add("%s%s" % (v['icon'], verticals_data[vertical]['color']))
    data = []
    for icon_color_string in icons_to_generate:
        icon_name, color_hex = icon_color_string.split('#')
        data.append({'icon': icon_name, 'color': '#%s' % color_hex})
    json.dump(data, open(os.path.join(current_dir, 'tmp', 'icons.json'), 'w'), indent=2, sort_keys=True, separators=(',', ': '))