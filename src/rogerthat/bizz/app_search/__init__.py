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

from rogerthat.bizz.app_search.models import AppSearch
from rogerthat.bizz.app_search.search import suggest_items, index_app_search
from rogerthat.dal.profile import get_user_profile
from rogerthat.to.system import GetAppSearchSuggestionsResponseTO,\
    AppSearchSuggestionActionTO


def get_search_suggestions(app_user, qry):
    result = GetAppSearchSuggestionsResponseTO(items=[])
    user_profile = get_user_profile(app_user)
    if not user_profile:
        return result

    app_search = AppSearch.create_key(user_profile.community_id, user_profile.home_screen_id).get()
    if not app_search:
        return result

    uids = suggest_items(qry, user_profile.community_id, user_profile.home_screen_id)
    for uid in uids:
        item = app_search.get_item_by_uid(uid)
        if not item:
            continue
        result.items.append(AppSearchSuggestionActionTO(title=item.title,
                                                        description=item.description,
                                                        icon=item.icon,
                                                        action=item.action))
    return result


def update_app_search(community_id, home_screen_id, items):
    app_search = AppSearch.create_key(community_id, home_screen_id).get()
    if app_search:
        all_uids_incuding_just_removed_once = [item.uid for item in app_search.items]
    else:
        all_uids_incuding_just_removed_once = []

    app_search = AppSearch(key=AppSearch.create_key(community_id, home_screen_id))
    app_search.items = []
    for item in items:
        if item.uid not in all_uids_incuding_just_removed_once:
            all_uids_incuding_just_removed_once.append(item.uid)
        app_search.items.append(items)
    app_search.put()

    index_app_search(app_search, all_uids_incuding_just_removed_once)