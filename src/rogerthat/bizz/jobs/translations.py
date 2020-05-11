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

import logging

__all__ = [ 'localize', 'SUPPORTED_LANGUAGES' ]

DEFAULT_LANGUAGE = "nl"

# TODO move this to normal translations


def localize(lang, key, **kwargs):
    if not lang:
        lang = DEFAULT_LANGUAGE
    lang = lang.replace('-', '_')
    if lang not in D:
        if '_' in lang:
            lang = lang.split('_')[0]
            if lang not in D:
                lang = DEFAULT_LANGUAGE
        else:
            lang = DEFAULT_LANGUAGE
    langdict = D[lang]
    if key not in langdict:
        # Fall back to default language
        if lang != DEFAULT_LANGUAGE:
            logging.warn("Translation key %s not found in language %s - fallback to default" % (key, lang))
            lang = DEFAULT_LANGUAGE
            langdict = D[lang]
    if key in langdict:
        return langdict[key] % kwargs
    logging.warn("Translation key %s not found in default language. Fallback to key" % key)
    return unicode(key) % kwargs

D = { }

D["nl"] = {
    """contract_type_001""": u"""Vast""",
    """contract_type_002""": u"""Tijdelijk""",
    """contract_type_003""": u"""Jongerenjobs""",
    """contract_type_004""": u"""Freelance""",
    """contract_type_005""": u"""Flexijob""",
    """contract_type_006""": u"""Dienstenchequebaan""",
    """contract_type_007""": u"""Vrijwilligerswerk""",

    """job_domain_001""": u"""Aankoop""",
    """job_domain_002""": u"""Administratie""",
    """job_domain_003""": u"""Bouw""",
    """job_domain_004""": u"""Communicatie""",
    """job_domain_005""": u"""Creatief""",
    """job_domain_006""": u"""Financieel""",
    """job_domain_007""": u"""Gezondheid""",
    """job_domain_008""": u"""Horeca en toerisme""",
    """job_domain_009""": u"""Human resources""",
    """job_domain_010""": u"""ICT""",
    """job_domain_011""": u"""Juridisch""",
    """job_domain_012""": u"""Land- en tuinbouw""",
    """job_domain_013""": u"""Logistiek en transport""",
    """job_domain_014""": u"""Dienstverlening""",
    """job_domain_015""": u"""Management""",
    """job_domain_016""": u"""Marketing""",
    """job_domain_017""": u"""Onderhoud""",
    """job_domain_018""": u"""Onderwijs""",
    """job_domain_019""": u"""Overheid""",
    """job_domain_020""": u"""Onderzoek en ontwikkeling""",
    """job_domain_021""": u"""Productie""",
    """job_domain_022""": u"""Techniek""",
    """job_domain_023""": u"""Verkoop""",
    """job_domain_024""": u"""Andere""",

}

# Keep this line at the bottom
SUPPORTED_LANGUAGES = D.keys()
