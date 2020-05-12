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

from rogerthat.bizz.job import run_job
from rogerthat.bizz.service import QR_TEMPLATE_BLUE_PACIFIC, QR_TEMPLATE_BROWN_BAG, QR_TEMPLATE_PINK_PANTHER, \
    QR_TEMPLATE_BLACK_HAND, create_default_qr_templates
from rogerthat.dal import parent_key
from rogerthat.models import ServiceProfile, QRTemplate
from google.appengine.ext import db


def redesign_qr_codes():
    run_job(_get_all_services, [], _update_qr_code_design, [])

def _get_all_services():
    return ServiceProfile.all(keys_only=True)

def _update_qr_code_design(sp_key):
    sp = db.get(sp_key)

    for template in QRTemplate.gql("WHERE deleted = False AND ANCESTOR is :1", parent_key(sp.service_user)):
        if template.description == QR_TEMPLATE_BLUE_PACIFIC or template.description == QR_TEMPLATE_BROWN_BAG or \
        template.description == QR_TEMPLATE_PINK_PANTHER or template.description == QR_TEMPLATE_BLACK_HAND:
            template.deleted = True
            template.put()

    create_default_qr_templates(sp.service_user)
