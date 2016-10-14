#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2016 Mobicage NV
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# @@license_version:1.1@@
# Crappy code to place a circle background behind icons, and make the icon itself transparent instead of black
import os
from PIL import Image, ImageDraw
from datetime import datetime

from mcfw.imaging import recolor_png

folder = '/home/lucas/git/rogerthat-backend/src/rogerthat/bizz/service/icons/512'

for subdir, dirs, files in os.walk(folder):
    for file in files:
        filepath = subdir + os.sep + file
        if filepath.endswith('.png'):
            with open(filepath) as f:
                print 'converting %s' % file
                file_content = f.read()
                # black to red
                is_big = '512' in filepath
                png_bytes = recolor_png(file_content, (0, 0, 0), (255, 0, 255))
                tmp_filename = '/tmp/temp%d.png' % datetime.now().microsecond
                with open(tmp_filename, 'w') as tmp:
                    percentage = .66666666666
                    size = int(percentage * 512) if is_big else int(percentage * 50)
                    tmp.write(png_bytes)

                icon = Image.open(tmp_filename)
                icon = icon.resize((size, size))
                pixdata = icon.load()

                for y in xrange(icon.size[1]):
                    for x in xrange(icon.size[0]):
                        if pixdata[x, y] == (0, 0, 0, 0):
                            pixdata[x, y] = (0, 0, 0, 255)
                        else:
                            pixdata[x, y] = (0, 0, 0, 0)
                icon.save(tmp_filename)
                img_w, img_h = icon.size
                if is_big:
                    r = 256
                else:
                    r = 25
                background = Image.new('RGBA', (r * 2, r * 2), None)
                draw = ImageDraw.Draw(background)
                x = y = r
                draw.ellipse((x - r, y - r, x + r, y + r), fill=(0, 0, 0, 255))
                temp = Image.open(tmp_filename)
                bg_w, bg_h = background.size
                offset = ((bg_w - img_w) / 2, (bg_h - img_h) / 2)
                background.paste(temp, offset)
                background.save('/home/lucas/icons/%s/fa-%s' % (r * 2, file))

# import sys
# import os
#
# sys.path.append('/home/lucas/git/rogerthat-build/src/')
# import app_utils
#
# # Convert 512 px (original, non-fa) icons to 50
# for subdir, dirs, files in os.walk(folder):
#     for file in files:
#         filepath = subdir + os.sep + file
#         if file.startswith('fa-'):
#             continue
#         new_filepath = '/home/lucas/icons/50/' + file
#         print 'Converting ' + file
#         app_utils.resize_image(filepath, new_filepath, 50, 50)
