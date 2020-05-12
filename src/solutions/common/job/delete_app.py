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

from google.appengine.api import users as gusers

from rogerthat.bizz.app import get_app
from rogerthat.bizz.job import run_job
from rogerthat.bizz.user import archiveUserDataAfterDisconnect
from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.dal.friend import get_friends_map
from rogerthat.models import UserProfile
from rogerthat.utils.cloud_tasks import create_task, schedule_tasks
from rogerthat.utils.transactions import run_in_xg_transaction
from shop.bizz import post_app_broadcast, put_service, put_shop_app
from shop.business.order import cancel_subscription
from shop.models import Customer
from shop.view import _get_service
from solution_server_settings import get_solution_server_settings


def _1_send_goodbye_message(app_id, message):
    app = get_app(app_id)
    message = message % {'app': app.name}
    post_app_broadcast(app.main_service, [app_id], message)


def _2_gather_emails(app_id):
    return [str(c.user_email) for c in Customer.list_by_app_id(app_id)]


def _3_set_app_disabled(app_id):
    app = get_app(app_id)
    app.disabled = True
    app.put()
    put_shop_app(app_id, False, False)


def _4_disable_all_customers(app_id, reason, dry_run=True):
    customers = Customer.list_by_app_id(app_id)
    to_cancel = []
    to_remove_app = []
    for c in customers:
        if c.default_app_id == app_id:
            to_cancel.append(c)
        else:
            to_remove_app.append(c)
    if dry_run:
        return {
            'to cancel': [(c.name, c.app_ids) for c in to_cancel],
            'to remove app': [(c.name, c.app_ids) for c in to_remove_app],
        }

    tasks = [create_task(cancel_subscription, c.id, cancel_reason=reason, immediately=True) for c in to_cancel]
    schedule_tasks(tasks, MIGRATION_QUEUE)
    tasks = [create_task(_remove_app_from_customer, c.id, app_id) for c in to_remove_app]
    schedule_tasks(tasks, MIGRATION_QUEUE)


def _5_unregister_accounts(app_id, unregister_text):
    run_job(_get_profiles, [app_id], _delete_account, [unregister_text], worker_queue=MIGRATION_QUEUE)


def _get_profiles(app_id):
    return UserProfile.list_by_app(app_id)


def _delete_account(profile, unregister_reason):
    # type: (UserProfile, unicode) -> None
    app_user = profile.user
    friend_map = get_friends_map(app_user)
    archiveUserDataAfterDisconnect(app_user, friend_map, profile, hard_delete=True, unregister_reason=unregister_reason)


def _remove_app_from_customer(customer_id, app_id):
    admin = get_solution_server_settings().shop_bizz_admin_emails[0]
    service = _get_service(customer_id, gusers.User(admin))
    service.apps = [app for app in service.apps if app != app_id]
    run_in_xg_transaction(put_service, customer_id, service, broadcast_to_users=[])
