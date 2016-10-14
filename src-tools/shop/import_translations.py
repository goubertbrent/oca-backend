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

from argparse import ArgumentParser
import hashlib
import os
from pprint import pformat
import sys


CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))

COLUMN_KEY = 2
COLUMN_TO_BE_TRANSLATED = 0
COLUMN_TRANSLATION = 1


def sha256_hex(val):
    d = hashlib.sha256()
    d.update(val if not isinstance(val, unicode) else val.encode('utf-8'))
    return d.hexdigest()


def get_language_code(lang_str):
    return lang_str.split(' - ')[0]


def import_translations(filename, translations):
    import xlrd  # @UnresolvedImport
    DEFAULT_LANGUAGE = u"nl"

    translation_keys_dict = { sha256_hex(key) : key for key in translations[DEFAULT_LANGUAGE] }

    book = xlrd.open_workbook(filename)
    for sheet in book.sheets():
        lang = get_language_code(sheet.name)
        for i in xrange(2, sheet.nrows):
            xls_row = sheet.row(i)
            if not any([x.value for x in xls_row]):
                continue  # Empty row

            xls_translation = unicode(xls_row[COLUMN_TRANSLATION].value)
            xls_key = unicode(xls_row[COLUMN_KEY].value)

            if xls_key in translation_keys_dict and xls_translation:
                translations[lang][translation_keys_dict[xls_key]] = xls_translation


def main(filename, translation_type):
    sys.path.append(os.path.join(CURRENT_DIR, '..', '..', 'src'))

    if translation_type == 'shop_translations':
        from shop.translations import shop_translations
        import_translations(filename, shop_translations)

        print "shop_translations = \\"
        print pformat(shop_translations)

    else:
        raise Exception('Unknown translation type: ' % translation_type)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('file', help='excel file name')
    parser.add_argument('type', choices=['shop_translations'])
    args = parser.parse_args()

    main(args.file, args.type)
