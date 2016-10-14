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

import hashlib
import os
import sys
import time

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))

COLUMN_KEY = 2
COLUMN_TO_BE_TRANSLATED = 0
COLUMN_TRANSLATION = 1

def lang_str(lang):
    from babel.core import Locale  # @UnresolvedImport
    return '%s - %s' % (lang, Locale(lang).english_name)


def sha256_hex(val):
    d = hashlib.sha256()
    d.update(val if not isinstance(val, unicode) else val.encode('utf-8'))
    return d.hexdigest()


def export(languages, translations, translations_type):
    import xlwt  # @UnresolvedImport
    DEFAULT_LANGUAGE = u"en"
    bold_style = xlwt.XFStyle()
    bold_style.font.bold = True

    book = xlwt.Workbook(encoding="utf-8")

    keys = [x[0] for x in sorted(translations[DEFAULT_LANGUAGE].iteritems(),
                                 key=lambda x: x[1].lower())]

    for lang, translations_dict in sorted(translations.iteritems()):
        if lang == DEFAULT_LANGUAGE or (languages and lang not in languages):
            continue

        sheet = book.add_sheet(lang_str(lang))
        sheet.write(0, COLUMN_TO_BE_TRANSLATED, lang_str(DEFAULT_LANGUAGE), bold_style)
        sheet.write(0, COLUMN_TRANSLATION, lang_str(lang), bold_style)
        sheet.write(0, COLUMN_KEY, "Key (do not change or remove)", bold_style)
        sheet.col(COLUMN_KEY).width = 20000
        sheet.col(COLUMN_TO_BE_TRANSLATED).width = 20000
        sheet.col(COLUMN_TRANSLATION).width = 20000

        for i, key in enumerate(keys):
            row = i + 2
            sheet.write(row, COLUMN_TO_BE_TRANSLATED, translations[DEFAULT_LANGUAGE][key])
            sheet.write(row, COLUMN_TRANSLATION, translations_dict.get(key, ''))
            sheet.write(row, COLUMN_KEY, sha256_hex(key))

    filename = 'SHOP-%s-%s.xls' % (translations_type, time.strftime("%Y-%m-%d--%H-%M-%S", time.gmtime(time.time())))
    dest = os.path.join(CURRENT_DIR, filename)
    with open(dest, 'w+') as f:
        book.save(f)
    print 'Exported translations to', dest

def main(languages):
    sys.path.append(os.path.join(CURRENT_DIR, '..', '..', 'src'))

    from shop.translations import shop_translations
    export(languages, shop_translations, 'shop_translations')

if __name__ == '__main__':
    languages = sys.argv[1:]
    main(languages)
