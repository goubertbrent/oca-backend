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

import logging

from solutions import translate as common_translate


def localize(lang, key, **kwargs):
    if not lang:
        lang = 'nl'
    if key not in MAPPING:
        logging.warn("Translation key %s not found in mapping. Fallback to key" % key)
        return key

    return common_translate(lang, MAPPING[key], **kwargs)


MAPPING = {
    """contract_type_001""": u"""oca.fulltime""",
    """contract_type_002""": u"""oca.temporary""",
    """contract_type_003""": u"""oca.youth_jobs""",
    """contract_type_004""": u"""oca.freelance""",
    """contract_type_005""": u"""oca.flexijob""",
    """contract_type_006""": u"""oca.service_check_job""",
    """contract_type_007""": u"""oca.volunteer_work""",

    """job_domain_001""": u"""oca.purchase""",
    """job_domain_002""": u"""oca.administration""",
    """job_domain_003""": u"""oca.construction""",
    """job_domain_004""": u"""oca.communication""",
    """job_domain_005""": u"""oca.creative""",
    """job_domain_006""": u"""oca.financial""",
    """job_domain_007""": u"""oca.health""",
    """job_domain_008""": u"""oca.hospitality_and_tourism""",
    """job_domain_009""": u"""oca.human_resources""",
    """job_domain_010""": u"""oca.ict""",
    """job_domain_011""": u"""oca.legal""",
    """job_domain_012""": u"""oca.agriculture_and_horticulture""",
    """job_domain_013""": u"""oca.logistics_and_transport""",
    """job_domain_014""": u"""oca.services""",
    """job_domain_015""": u"""oca.management""",
    """job_domain_016""": u"""oca.marketing""",
    """job_domain_017""": u"""oca.maintenance""",
    """job_domain_018""": u"""oca.education""",
    """job_domain_019""": u"""oca.government""",
    """job_domain_020""": u"""oca.research_and_development""",
    """job_domain_021""": u"""oca.production""",
    """job_domain_022""": u"""oca.technic""",
    """job_domain_023""": u"""oca.sale""",
    """job_domain_024""": u"""oca.others""",
}
