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

import base64
from os import path
from zipfile import ZipFile, ZIP_DEFLATED

from mcfw.rpc import returns, arguments
from rogerthat.to.branding import BrandingTO
from solutions.common.bizz import put_branding
from solutions.common.models import SolutionMainBranding


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

@returns(BrandingTO)
@arguments(branding=SolutionMainBranding, description=unicode, nuntiuz_message_replacement=unicode, files=[unicode])
def generate_branding(branding, description, nuntiuz_message_replacement, files=None):
    nuntiuz_message_replacement = nuntiuz_message_replacement.encode('utf-8')
    branding_stream = StringIO(branding.blob)
    zip_file = ZipFile(branding_stream)
    try:
        new_zip_stream = StringIO()
        new_zip = ZipFile(new_zip_stream, 'w', compression=ZIP_DEFLATED)
        try:
            for file_name in set(zip_file.namelist()):
                html = zip_file.read(file_name)
                html = html.replace('<nuntiuz_message/>', nuntiuz_message_replacement)
                file_name = file_name if file_name != 'branding.html' else 'app.html'  # rename branding.html to app.html
                new_zip.writestr(file_name, html)
            if files:
                for filename in files:
                    new_zip.write(filename, path.basename(filename))
        finally:
            new_zip.close()
    finally:
        zip_file.close()

    return put_branding(description, base64.b64encode(new_zip_stream.getvalue()))
