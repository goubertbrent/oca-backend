# -*- coding: utf-8 -*-
# Copyright 2020 Green Valley Belgium NV
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
# @@license_version:1.7@@

from StringIO import StringIO
from contextlib import closing
import io
import logging
import threading

from google.appengine.api.images import TOP_LEFT, BadRequestError, ANCHOR_TYPES,\
    composite
from google.appengine.api.images.images_service_pb import CompositeImageOptions

from PIL import Image
from rogerthat.consts import DEBUG


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
            layers = [(png_bytes, 0, 0, 1.0, TOP_LEFT),
                      (overlay, 0, 0, 1.0, TOP_LEFT)]
            if sample_overlay:
                layers.append((sample_overlay, 0, 0, 1.0, TOP_LEFT))
            if DEBUG:
                return composite_debug(layers, 348, 343)
            return composite(layers, 348, 343)
        else:
            layers = [(png_bytes, 0, 0, 1.0, TOP_LEFT)]
            if sample_overlay:
                layers.append((sample_overlay, 0, 0, 1.0, TOP_LEFT))
            if DEBUG:
                return composite_debug(layers, 348, 343, color=4294967295)
            return composite(layers, 330, 330, color=4294967295)

def _ArgbToRgbaTuple(argb):
    """Convert from a single ARGB value to a tuple containing RGBA.

    Args:
        argb: Signed 32 bit integer containing an ARGB value.

    Returns:
        RGBA tuple.
    """

    unsigned_argb = argb % 0x100000000
    return ((unsigned_argb >> 16) & 0xFF,
            (unsigned_argb >> 8) & 0xFF,
            unsigned_argb & 0xFF,
            (unsigned_argb >> 24) & 0xFF)


def _BackendPremultiplication(color):
    """Apply premultiplication and unpremultiplication to match production.

    Args:
        color: color tuple as returned by _ArgbToRgbaTuple.

    Returns:
        RGBA tuple.
    """

    alpha = color[3]
    rgb = color[0:3]
    multiplied = [(x * (alpha + 1)) >> 8 for x in rgb]
    if alpha:
        alpha_inverse = 0xffffff / alpha
        unmultiplied = [(x * alpha_inverse) >> 16 for x in multiplied]
    else:
        unmultiplied = [0] * 3
    return tuple(unmultiplied + [alpha])


def composite_debug(inputs, width, height, color=0):
    MAX_COMPOSITES_PER_REQUEST = 16

    if (not isinstance(width, (int, long)) or not isinstance(height, (int, long)) or not isinstance(color, (int, long))):
        raise TypeError("Width, height and color must be integers.")

    if not inputs:
        raise BadRequestError("Must provide at least one input")
    if len(inputs) > MAX_COMPOSITES_PER_REQUEST:
        raise BadRequestError("A maximum of %d composition operations can be performed in a single request" % MAX_COMPOSITES_PER_REQUEST)

    if width <= 0 or height <= 0:
        raise BadRequestError("Width and height must be > 0.")
    if width > 4000 or height > 4000:
        raise BadRequestError("Width and height must be <= 4000.")

    if color > 0xffffffff or color < 0:
        raise BadRequestError("Invalid color")

    if color >= 0x80000000:
        color -= 0x100000000

    color = _ArgbToRgbaTuple(color)
    color = _BackendPremultiplication(color)

    canvas = Image.new('RGBA', (width, height), color)

    for (image, x, y, opacity, anchor) in inputs:
        if not image:
            raise BadRequestError("Each input must include an image")
        if (not isinstance(x, (int, long)) or not isinstance(y, (int, long)) or not isinstance(opacity, (float))):
            raise TypeError("x_offset, y_offset must be integers and opacity must be a float")
        if x > 4000 or x < -4000:
            raise BadRequestError("xOffsets must be in range [-4000, 4000]")
        if y > 4000 or y < -4000:
            raise BadRequestError("yOffsets must be in range [-4000, 4000]")
        if opacity < 0 or opacity > 1:
            raise BadRequestError("Opacity must be in the range 0.0 to 1.0")
        if anchor not in ANCHOR_TYPES:
            raise BadRequestError("Anchor type '%s' not in recognized set %s" % (anchor, ANCHOR_TYPES))

        source = Image.open(StringIO(image))

        options = CompositeImageOptions()
        options.set_x_offset(x)
        options.set_y_offset(y)
        options.set_opacity(opacity)
        options.set_anchor(anchor)

        x_anchor = (options.anchor() % 3) * 0.5
        y_anchor = (options.anchor() / 3) * 0.5
        x_offset = int(options.x_offset() + x_anchor * (width - source.size[0]))
        y_offset = int(options.y_offset() + y_anchor * (height - source.size[1]))
        if source.mode == 'RGBA':
            canvas.paste(source, (x_offset, y_offset), source)
        else:
            # Fix here: alpha must be an integer (and not a float)
            alpha = int(options.opacity() * 255)
            mask = Image.new('L', source.size, alpha)
            canvas.paste(source, (x_offset, y_offset), mask)

    out = StringIO()
    canvas.save(out, 'png')
    return out.getvalue()


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
