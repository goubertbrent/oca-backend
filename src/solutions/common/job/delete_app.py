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

from rogerthat.bizz.app import get_app
from rogerthat.bizz.job import run_job
from rogerthat.bizz.user import delete_user_data
from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.dal.friend import get_friends_map
from rogerthat.models import UserProfile
from rogerthat.utils.cloud_tasks import create_task, schedule_tasks
from shop.business.order import cancel_subscription
from shop.models import Customer
from rogerthat.bizz.communities.communities import get_community


def _3_set_app_disabled(app_id, community_id):
    app = get_app(app_id)
    app.disabled = True
    app.put()

    community = get_community(community_id)
    community.signup_enabled = False
    community.features = []
    community.put()


def _4_disable_all_customers(community_id, reason, dry_run=True):
    customers = Customer.list_by_community_id(community_id)
    to_cancel = []
    for c in customers:
        to_cancel.append(c)
    if dry_run:
        return [c.name for c in to_cancel]

    tasks = [create_task(cancel_subscription, c.id, cancel_reason=reason) for c in to_cancel]
    schedule_tasks(tasks, MIGRATION_QUEUE)


def _5_unregister_accounts(community_id, unregister_text):
    run_job(_get_profiles, [community_id], _delete_account, [unregister_text], worker_queue=MIGRATION_QUEUE)


def _get_profiles(community_id):
    return UserProfile.list_by_community(community_id)


def _delete_account(profile, unregister_reason):
    # type: (UserProfile, unicode) -> None
    app_user = profile.user
    friend_map = get_friends_map(app_user)
    delete_user_data(app_user, friend_map, profile, unregister_reason=unregister_reason)
