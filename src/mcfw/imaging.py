# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
# NOTICE: THIS FILE HAS BEEN MODIFIED BY GREEN VALLEY BELGIUM NV IN ACCORDANCE WITH THE APACHE LICENSE VERSION 2.0
# Copyright 2018 GIG Technology NV
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
# @@license_version:1.6@@

from StringIO import StringIO
from contextlib import closing
import io
import logging
import threading

from PIL import Image
from google.appengine.api.images import composite, TOP_LEFT

generate_image_rlock = threading.RLock()


def generate_qr_code(content, overlay, color, sample_overlay, svg=False):
    import qrcode
    from qrcode.image.pure import PymagingImage
    from qrcode.image.svg import SvgImage
    if svg:
        factory = SvgImage
        img = qrcode.make(content, image_factory=factory)
        stream = StringIO()
        try:
            img.save(stream)
            return stream.getvalue()
        finally:
            stream.close()
    else:
        def generate_image(error_correction):

            with generate_image_rlock:
                # Generate the QR-code in a synchronized block because the qrcode lib is not
                # thread safe
                qr = qrcode.QRCode(
                        version=1,
                        error_correction=error_correction,
                        box_size=10,
                        border=4,
                )
                qr.add_data(content)
                qr.make()
                img = qr.make_image(image_factory=PymagingImage)
                stream = StringIO()
                try:
                    img.save(stream)
                    return stream.getvalue()
                finally:
                    stream.close()

        png_bytes = generate_image(error_correction=qrcode.constants.ERROR_CORRECT_M)
        png_size = get_png_size(png_bytes)
        logging.debug("Size of QR with quality M: %s", png_size)
        if png_size[0] > 330 or png_size[1] > 330:
            png_bytes = generate_image(error_correction=qrcode.constants.ERROR_CORRECT_L)
            png_size = get_png_size(png_bytes)
            logging.debug("Size of QR with quality L: %s", png_size)
        elif png_size[0] < 330 and png_size[1] < 330:
            png_bytes = generate_image(error_correction=qrcode.constants.ERROR_CORRECT_H)
            png_size = get_png_size(png_bytes)
            logging.debug("Size of QR with quality H: %s", png_size)
            if png_size[0] < 330 and png_size[1] < 330:
                png_bytes = generate_image(error_correction=qrcode.constants.ERROR_CORRECT_Q)
                png_size = get_png_size(png_bytes)
                logging.debug("Size of QR with quality Q: %s", png_size)

        if png_size[0] != 330 and png_size[1] != 330:
            with closing(StringIO(png_bytes)) as f:
                img = Image.open(f)
                img = img.resize((330, 330), Image.ANTIALIAS)
            with closing(io.BytesIO()) as bytes_io:
                img.save(bytes_io, format='PNG')
                png_bytes = bytes_io.getvalue()
                png_size = get_png_size(png_bytes)
                logging.info("Resized QR to %s", png_size)

        if png_size[0] != 330 and png_size[1] != 330:
            raise ValueError("Unable to generate correct QR code (content: %s)" % content)

        png_bytes = recolor_png(png_bytes, (0, 0, 0), tuple(color))

        if overlay:
            layers = [(png_bytes, 0, 0, 1.0, TOP_LEFT), (overlay, 0, 0, 1.0, TOP_LEFT)]
            if sample_overlay:
                layers.append((sample_overlay, 0, 0, 1.0, TOP_LEFT))
            return composite(layers, 348, 343)
        else:
            layers = [(png_bytes, 0, 0, 1.0, TOP_LEFT)]
            if sample_overlay:
                layers.append((sample_overlay, 0, 0, 1.0, TOP_LEFT))
            return composite(layers, 330, 330, color=4294967295)


def get_png_size(png_bytes):
    from rogerthat.utils import png

    r = png.Reader(file=StringIO(str(png_bytes)))
    p = r.read()
    return p[-1]['size']


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
