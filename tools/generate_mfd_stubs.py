#!/usr/bin/env python
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

import os

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
MFD_DIR = os.path.join(CURRENT_DIR, '..', 'src', 'rogerthat', 'bizz', 'service', 'mfd')
GEN_FILE = os.path.join(MFD_DIR, 'gen.py')
SUB_FILE = os.path.join(MFD_DIR, 'sub.py')


def replace(to_be_replaced, replacement, content):
    return content.replace(to_be_replaced, replacement)


def add_line(index, line, content):
    lines = content.splitlines()
    lines.insert(index, line)
    content = '\n'.join(lines)
    return content


def main():
# Install generateDS from http://dev.mobicage.com/fileshare/downloads/appengine-dev-tools/generateDS-2.7a.tar.gz
# Untar
#
# go into generateDS-2.7a directory
# ./generateDS.py --external-encoding='utf-8' -o ../rogerthat-backend/src/rogerthat/bizz/service/mfd/gen.py -s ../rogerthat-backend/src/rogerthat/bizz/service/mfd/sub.py ../rogerthat-backend/src/rogerthat/service/api/MessageFlow.1.xsd

    with open(GEN_FILE, 'r') as f:
        gen_content = f.read()
    with open(SUB_FILE, 'r') as f:
        sub_content = f.read()

    sub_content = replace('import ??? as supermod',
                          'from rogerthat.bizz.service.mfd import gen as supermod',
                          sub_content)

    gen_content = add_line(10, 'from rogerthat.utils import xml_escape', gen_content)

    gen_content = replace('outfile.write(str(self.valueOf_).encode(ExternalEncoding))',
                          'outfile.write(unicode(xml_escape(self.valueOf_)).encode(ExternalEncoding))',
                          gen_content)

    gen_content = add_line(2, '# @PydevCodeAnalysisIgnore', gen_content)
    gen_content = add_line(1, '# @@xxx_skip_license@@', gen_content)

    sub_content = add_line(1, '# @PydevCodeAnalysisIgnore', sub_content)
    sub_content = add_line(1, '# @@xxx_skip_license@@', sub_content)

    with open(GEN_FILE, 'w') as f:
        f.write(gen_content)
    with open(SUB_FILE, 'w') as f:
        f.write(sub_content)

if __name__ == "__main__":
    main()
