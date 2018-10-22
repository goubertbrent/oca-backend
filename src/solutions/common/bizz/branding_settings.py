# -*- coding: utf-8 -*-
# Copyright 2018 Mobicage NV
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
# @@license_version:1.3@@

from google.appengine.ext import db

from mcfw.rpc import returns, arguments
from rogerthat.dal import put_and_invalidate_cache
from rogerthat.rpc import users
from rogerthat.utils import now
from rogerthat.utils.transactions import on_trans_committed
from solutions.common.bizz import broadcast_updates_pending
from solutions.common.models import SolutionSettings, SolutionBrandingSettings
from solutions.common.models.group_purchase import SolutionGroupPurchaseSettings
from solutions.common.models.loyalty import SolutionLoyaltySettings
from solutions.common.models.static_content import SolutionStaticContent
from solutions.common.to import BrandingSettingsTO


@returns()
@arguments(service_user=users.User, branding_settings_to=BrandingSettingsTO)
def save_branding_settings(service_user, branding_settings_to):
    """
    Args:
        service_user (users.User)
        branding_settings_to (BrandingSettingsTO)
    """

    def trans():
        branding_settings, sln_settings, loyalty_settings = db.get((SolutionBrandingSettings.create_key(service_user),
                                                                    SolutionSettings.create_key(service_user),
                                                                    SolutionLoyaltySettings.create_key(service_user)))

        if not branding_settings:
            branding_settings = SolutionBrandingSettings(key=SolutionBrandingSettings.create_key(service_user))
        branding_settings_to.color_scheme = u'light'
        branding_settings_to.background_color = SolutionBrandingSettings.default_background_color(
            branding_settings_to.color_scheme)
        branding_settings_to.text_color = SolutionBrandingSettings.default_text_color(branding_settings_to.color_scheme)

        branding_settings.background_color = branding_settings_to.background_color
        branding_settings.color_scheme = branding_settings_to.color_scheme
        branding_settings.menu_item_color = branding_settings_to.menu_item_color
        branding_settings.text_color = branding_settings_to.text_color
        branding_settings.show_identity_name = branding_settings_to.show_identity_name
        branding_settings.show_avatar = branding_settings_to.show_avatar
        branding_settings.recommend_enabled = branding_settings_to.recommend_enabled

        branding_settings.modification_time = now()

        sln_settings.events_branding_hash = None
        sln_settings.updates_pending = True

        to_be_put = [branding_settings, sln_settings]

        if branding_settings_to.left_align_icons != branding_settings.left_align_icons:
            static_content = SolutionStaticContent.list_non_deleted(service_user)
            for static_content  in SolutionStaticContent.list_non_deleted(service_user):
                static_content.provisioned = False
                to_be_put.append(static_content)
            branding_settings.left_align_icons = branding_settings_to.left_align_icons

        if loyalty_settings:
            loyalty_settings.loyalty_branding_hash = None
            to_be_put.append(loyalty_settings)
        sgps = SolutionGroupPurchaseSettings.get(SolutionGroupPurchaseSettings.create_key(service_user, sln_settings.solution))
        if sgps:
            sgps.branding_hash = None
            to_be_put.append(sgps)

        put_and_invalidate_cache(*to_be_put)
        on_trans_committed(broadcast_updates_pending, sln_settings)

    xg_on = db.create_transaction_options(xg=True)
    db.run_in_transaction_options(xg_on, trans)
