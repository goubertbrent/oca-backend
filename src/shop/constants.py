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

from rogerthat.rpc import users

MAPS_QUEUE = "maps-queue"
MAPS_CONTROLLER_QUEUE = "maps-controller-queue"

# located in shop/html/img/
LOGO_LANGUAGES = ['nl', 'en', 'fr']


COUNTRY_DEFAULT_LANGUAGES = {
    u'BE': u'nl',
    u'NL': u'nl',
    u'FR': u'fr',
    u'DE': u'de',
    u'ES': u'es',
    u'RO': u'ro',
    u'MX': u'es',
    u'BR': u'pt_BR',
    u'CD': u'fr',
    u'RU': u'ru'
}

# Uncomment countries and languages when needed. Don't forget to add a default language for a country.

# ISO 639-1 Language Codes
OFFICIALLY_SUPPORTED_LANGUAGES = {
    u'en': u'English',
    # u'aa': u'Afar',
    # u'ab': u'Abkhazian',
    # u'af': u'Afrikaans',
    # u'am': u'Amharic',
    # u'ar': u'Arabic',
    # u'as': u'Assamese',
    # u'ay': u'Aymara',
    # u'az': u'Azerbaijani',
    # u'ba': u'Bashkir',
    # u'be': u'Byelorussian',
    # u'bg': u'Bulgarian',
    # u'bh': u'Bihari',
    # u'bi': u'Bislama',
    # u'bn': u'Bengali/Bangla',
    # u'bo': u'Tibetan',
    # u'br': u'Breton',
    # u'ca': u'Catalan',
    # u'co': u'Corsican',
    # u'cs': u'Czech',
    # u'cy': u'Welsh',
    # u'da': u'Danish',
    # u'de': u'German',
    # u'dz': u'Bhutani',
    # u'el': u'Greek',
    # u'eo': u'Esperanto',
    u'es': u'Spanish',
    # u'et': u'Estonian',
    # u'eu': u'Basque',
    # u'fa': u'Persian',
    # u'fi': u'Finnish',
    # u'fj': u'Fiji',
    # u'fo': u'Faeroese',
    u'fr': u'French',
    # u'fy': u'Frisian',
    # u'ga': u'Irish',
    # u'gd': u'Scots/Gaelic',
    # u'gl': u'Galician',
    # u'gn': u'Guarani',
    # u'gu': u'Gujarati',
    # u'ha': u'Hausa',
    # u'hi': u'Hindi',
    # u'hr': u'Croatian',
    # u'hu': u'Hungarian',
    # u'hy': u'Armenian',
    # u'ia': u'Interlingua',
    # u'ie': u'Interlingue',
    # u'ik': u'Inupiak',
    # u'in': u'Indonesian',
    # u'is': u'Icelandic',
    # u'it': u'Italian',
    # u'iw': u'Hebrew',
    # u'ja': u'Japanese',
    # u'ji': u'Yiddish',
    # u'jw': u'Javanese',
    # u'ka': u'Georgian',
    # u'kk': u'Kazakh',
    # u'kl': u'Greenlandic',
    # u'km': u'Cambodian',
    # u'kn': u'Kannada',
    # u'ko': u'Korean',
    # u'ks': u'Kashmiri',
    # u'ku': u'Kurdish',
    # u'ky': u'Kirghiz',
    # u'la': u'Latin',
    # u'ln': u'Lingala',
    # u'lo': u'Laothian',
    # u'lt': u'Lithuanian',
    # u'lv': u'Latvian/Lettish',
    # u'mg': u'Malagasy',
    # u'mi': u'Maori',
    # u'mk': u'Macedonian',
    # u'ml': u'Malayalam',
    # u'mn': u'Mongolian',
    # u'mo': u'Moldavian',
    # u'mr': u'Marathi',
    # u'ms': u'Malay',
    # u'mt': u'Maltese',
    # u'my': u'Burmese',
    # u'na': u'Nauru',
    # u'ne': u'Nepali',
    u'nl': u'Dutch',
    # u'no': u'Norwegian',
    # u'oc': u'Occitan',
    # u'om': u'(Afan)/Oromoor/Oriya',
    # u'pa': u'Punjabi',
    # u'pl': u'Polish',
    # u'ps': u'Pashto/Pushto',
    # u'pt': u'Portuguese',
    u'pt_BR': u'Portuguese (Brazil)',
    # u'qu': u'Quechua',
    # u'rm': u'Rhaeto-Romance',
    # u'rn': u'Kirundi',
    u'ro': u'Romanian',
    u'ru': u'Russian',
    # u'rw': u'Kinyarwanda',
    # u'sa': u'Sanskrit',
    # u'sd': u'Sindhi',
    # u'sg': u'Sangro',
    # u'sh': u'Serbo-Croatian',
    # u'si': u'Singhalese',
    # u'sk': u'Slovak',
    # u'sl': u'Slovenian',
    # u'sm': u'Samoan',
    # u'sn': u'Shona',
    # u'so': u'Somali',
    # u'sq': u'Albanian',
    # u'sr': u'Serbian',
    # u'ss': u'Siswati',
    # u'st': u'Sesotho',
    # u'su': u'Sundanese',
    # u'sv': u'Swedish',
    # u'sw': u'Swahili',
    # u'ta': u'Tamil',
    # u'te': u'Tegulu',
    # u'tg': u'Tajik',
    # u'th': u'Thai',
    # u'ti': u'Tigrinya',
    # u'tk': u'Turkmen',
    # u'tl': u'Tagalog',
    # u'tn': u'Setswana',
    # u'to': u'Tonga',
    # u'tr': u'Turkish',
    # u'ts': u'Tsonga',
    # u'tt': u'Tatar',
    # u'tw': u'Twi',
    # u'uk': u'Ukrainian',
    # u'ur': u'Urdu',
    # u'uz': u'Uzbek',
    # u'vi': u'Vietnamese',
    # u'vo': u'Volapuk',
    # u'wo': u'Wolof',
    # u'xh': u'Xhosa',
    # u'yo': u'Yoruba',
    # u'zh': u'Chinese',
    # u'zu': u'Zulu'
}
STORE_MANAGER = users.User(u'customers@shop')
