#!/usr/bin/env python
import os
import re
from PIL import Image
from StringIO import StringIO
import shutil
import json

def create_dir_if_not_exists(path):
    path = os.path.dirname(path)
    if not os.path.exists(path):
        os.makedirs(path)


def walklevel(d):
    for o in os.listdir(d):
        if os.path.isdir(os.path.join(d, o)):
            continue
        yield o


def parse_color(color):
    color = color.lstrip('#')
    if len(color) == 3:
        color = color[0] * 2 + color[1] * 2 + color[2] * 2
    m = re.match("^([a-fA-F0-9]{2})([a-fA-F0-9]{2})([a-fA-F0-9]{2})$", color)
    if not m:
        raise ValueError("%s is not a valid color." % color)
    return tuple(map(lambda x: int(x, 16), m.groups()))


def recolor_png(png_bytes, source_color, target_color):
    im = Image.open(StringIO(png_bytes))
    pixels = im.load()
    old_r, old_g, old_b = source_color
    new_r, new_g, new_b = target_color
    width, height = im.size
    for x in xrange(width):
        for y in xrange(height):
            rgba = pixels[x, y]
            if len(rgba) == 4:
                r, g, b, a = rgba
            else:
                r, g, b = rgba
                a = 255
            if (r, g, b) == (old_r, old_g, old_b):
                pixels[x, y] = (new_r, new_g, new_b, a)
    output = StringIO()
    im.save(output, format='png')
    return output.getvalue()


def recolor_pin(source_file, target_file, source_color, target_color):
    with open(target_file, 'w') as tf:
        with open(source_file) as sf:
            tf.write(recolor_png(sf.read(), source_color, target_color))


def merge_files(pin_file, source_dir, target_dir):
    for filename in walklevel(source_dir):
        source_file = os.path.join(source_dir, filename)
        target_file = os.path.join(target_dir, filename)
        create_dir_if_not_exists(target_file)
        make_pin(pin_file, source_file, target_file)


def make_pin(pin_file, source_img_file, target_img_file):
    image = Image.open(source_img_file)
    back_image = Image.open(pin_file)
    target_x = int((back_image.size[0]/ 2.0) - (image.size[0] / 2.0))
    back_image.paste(image, (target_x, target_x), mask=image)
    back_image.save(target_img_file)
    

if __name__ == '__main__':
    source_color = (0, 0, 0)
    root_dir =  os.path.join(os.path.dirname(__file__), 'tmp')
    icons_path = os.path.join(root_dir, 'icons.json')
    with open(icons_path, 'r') as f:
        items = json.load(f)

    create_dir_if_not_exists(os.path.join(root_dir, 'pins'))
    create_dir_if_not_exists(os.path.join(root_dir, 'output'))

    for item in items:
        stripped_color = item['color'].replace('#', '')
        pin_file = os.path.join(root_dir, 'pins', 'pin_' + stripped_color + '.png')
        target_color = parse_color(item['color'])
        recolor_pin('pin.png', pin_file, source_color, target_color)
        source_file = os.path.join(root_dir, 'fa_iconen', item['icon'].replace('fa-', '') + '.png')
        target_name = item['icon'] + '-' +  stripped_color + '.png'
        target_file =  os.path.join(root_dir, 'output', 'icons_v1_pins', target_name)
        make_pin(pin_file, source_file, target_file)

        target_file = os.path.join(root_dir, 'output', 'icons_v1_trans', target_name)
        shutil.copy2(source_file, target_file)