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
import time
from datetime import datetime
from google.appengine.ext import db, ndb
from google.appengine.ext.deferred import deferred
from typing import Set, Optional

from mcfw.rpc import serialize_complex_value
from rogerthat.bizz.communities.communities import get_community
from rogerthat.bizz.communities.models import AppFeatures
from rogerthat.consts import DAY, SCHEDULED_QUEUE
from rogerthat.dal.app import get_app_by_id
from rogerthat.dal.profile import get_service_profile
from rogerthat.dal.service import get_service_identity
from rogerthat.models import ServiceIdentity, ServiceProfile
from rogerthat.models.settings import ServiceInfo
from rogerthat.rpc import users
from rogerthat.to.service import UserDetailsTO
from rogerthat.utils import channel, log_offload, now, send_mail
from rogerthat.utils.service import create_service_identity_user
from rogerthat.utils.transactions import run_in_xg_transaction
from shop.models import CustomerSignup, Customer, CustomerSignupStatus
from shop.to import CustomerServiceTO
from solutions import translate as common_translate
from solutions.common.bizz import SolutionModule, common_provision
from solutions.common.bizz.campaignmonitor import send_smart_email
from solutions.common.bizz.inbox import add_solution_inbox_message, create_solution_inbox_message
from solutions.common.bizz.messaging import send_inbox_forwarders_message
from solutions.common.bizz.settings import get_service_info
from solutions.common.dal import get_solution_settings
from solutions.common.models import SolutionServiceConsent, SolutionServiceConsentHistory
from solutions.common.to import SolutionInboxMessageTO, ProvisionResponseTO

# signup smart emails with the countdown (seconds) they should be sent after a successfull registration
SMART_EMAILS_ID_COMPLETE_DASHBOARD = 'f98e0153-f295-412b-89a3-4d4cc6b95162'

SMART_EMAILS = {
    '8dd5fe5f-02eb-40f9-b9fa-9a48d52952b4': 1, # 1. Proficiat + opmaak & zichtbaar
    'e6b456af-a811-4540-903c-5135cd6e4802': 2 * DAY, # 2. NWSbericht aan&opmaken
    SMART_EMAILS_ID_COMPLETE_DASHBOARD: 3 * DAY, # Dashboard Aanvullen params: {'appName': 'stringValue'}
    #'c87c3b2c-e1e8-4680-914e-6f81f2bd37f5': 4 * DAY, # 3. Uw eigen reservatie-systeem
}


def get_allowed_modules(city_customer):
    # type: (Customer) -> Set[str]
    if city_customer.can_only_edit_organization_type(ServiceProfile.ORGANIZATION_TYPE_NON_PROFIT):
        return SolutionModule.ASSOCIATION_MODULES
    else:
        community = get_community(city_customer.community_id)
        allowed_modules = list(SolutionModule.POSSIBLE_MODULES)
        if AppFeatures.JOBS in community.features:
            allowed_modules.append(SolutionModule.JOBS)
        if AppFeatures.LOYALTY in community.features:
            allowed_modules.append(SolutionModule.LOYALTY)
        return set(allowed_modules)


def get_default_modules(city_customer):
    return [
        module for module in get_allowed_modules(city_customer) if module in CustomerSignup.DEFAULT_MODULES
    ]


def filter_modules(city_customer, modules):
    """Given a modules list, it will return the mandatory and allowed modules and discard others.

    Args:
        city_customer (Customer): city customer
        modules (list of unicode)
    """
    mods = [m for m in SolutionModule.MANDATORY_MODULES]
    mods.extend([m for m in modules if m in get_allowed_modules(city_customer)])
    modules = list(set(mods))
    return modules


def create_customer_with_service(city_customer, customer, service, name, address1, address2, zip_code,
                                 city, language,  organization_type, vat, website=None, facebook_page=None, force=False):
    """Given a customer and a service, will create the customer, contact and order."""
    from shop.bizz import put_customer_with_service
    customer_id = customer.id if customer else None
    if not customer and organization_type not in city_customer.editable_organization_types:
        organization_type = city_customer.editable_organization_types[0]

    return put_customer_with_service(service, name, address1, address2, zip_code, city, city_customer.country, language,
                                     organization_type, vat, customer_id,
                                     website, facebook_page, force=force)


def put_customer_service(customer, service, search_enabled, skip_email_check, rollback=False,
                         password=None, tos_version=None, send_login_information=False):
    # type: (Customer, CustomerServiceTO, bool, bool, bool, Optional[unicode], Optional[long], bool) -> ProvisionResponseTO
    """Put the service, if rollback is set, it will remove the customer in case of failure."""
    from shop.bizz import put_service
    customer_key = customer.key()

    def trans():
        return put_service(customer, service, search_enabled=search_enabled,
                           skip_email_check=skip_email_check, password=password, tos_version=tos_version,
                           send_login_information=send_login_information)

    try:
        return run_in_xg_transaction(trans)
    except Exception as e:
        if rollback:
            db.delete(db.GqlQuery("SELECT __key__ WHERE ANCESTOR IS KEY('%s')" % customer_key).fetch(None))
        logging.debug('Unhandled exception: %s', e, exc_info=True)
        raise e


def get_inbox_message_sender_details(sender_service_email):
    sender_settings = get_solution_settings(sender_service_email)
    sender_service_profile = get_service_profile(sender_service_email)
    return UserDetailsTO(email=sender_service_email.email(),
                         name=sender_settings.name,
                         avatar_url=sender_service_profile.avatarUrl,
                         language=sender_service_profile.defaultLanguage)


def new_inbox_message(sln_settings, message, parent_chat_key=None, service_identity=None, **kwargs):
    service_identity = service_identity or ServiceIdentity.DEFAULT
    service_user = sln_settings.service_user
    language = sln_settings.main_language
    send_to_forwarders = kwargs.pop('send_to_forwarders', False)

    user_details = kwargs.pop('user_details', None)
    sent_by_service = user_details is None
    if not user_details:  # sent by the service itself
        si = get_service_identity(create_service_identity_user(service_user, service_identity))
        user_details = UserDetailsTO.create(service_user.email(), si.name, language, si.avatarUrl, si.app_id)

    if not parent_chat_key:
        category = kwargs.pop('category', None)
        category_key = kwargs.pop('category_key', None)
        reply_enabled = kwargs.pop('reply_enabled', False)
        message = create_solution_inbox_message(service_user, service_identity, category, category_key,
                                                sent_by_service, [user_details], now(), message, reply_enabled,
                                                **kwargs)
    else:
        message, _ = add_solution_inbox_message(service_user, parent_chat_key, False, [user_details], now(),
                                                message, **kwargs)

    if send_to_forwarders:
        send_inbox_forwarders_message(service_user, service_identity, user_details.toAppUser(), message.message, {
            'if_name': user_details.name,
            'if_email': user_details.email
        }, message_key=message.solution_inbox_message_key, reply_enabled=message.reply_enabled)

    return message


def send_inbox_message_update(sln_settings, message, service_identity=None):
    service_user = sln_settings.service_user
    service_info = get_service_info(service_user, service_identity)
    channel.send_message(service_user, u'solutions.common.messaging.update',
                         message=SolutionInboxMessageTO.fromModel(message, sln_settings, service_info, True).to_dict(),
                         service_identity=service_identity)


def _send_signup_status_inbox_reply(sln_settings, parent_chat_key, approved, reason):
    lang = sln_settings.main_language
    if approved:
        message = common_translate(lang, u'approved')
    else:
        message = common_translate(lang, u'signup_request_denial_reason', reason=reason)

    inbox_message = new_inbox_message(sln_settings, message, parent_chat_key,
                                      mark_as_read=not approved,
                                      mark_as_trashed=approved)
    return inbox_message


def _schedule_signup_smart_emails(customer_email, app_name=None):
    for email_id, countdown in SMART_EMAILS.iteritems():
        data = None
        if email_id == SMART_EMAILS_ID_COMPLETE_DASHBOARD:
            if not app_name:
                continue
            data = {'appName': app_name}
        deferred.defer(send_smart_email, email_id, [customer_email], data=data,
                       _countdown=countdown,
                       _queue=SCHEDULED_QUEUE)


def _send_approved_signup_email(signup):
    if signup.parent().language == 'nl':
        _schedule_signup_smart_emails(signup.customer_email)


def _send_denied_signup_email(city_customer, signup, reason):
    subject = common_translate(signup.language, u'signup_request_denied_by_city', city=city_customer.name)
    lines = [
        common_translate(signup.language, 'dear_name', name=signup.customer_name),
        common_translate(signup.language, 'signup_request_denial_reason', reason=reason),
        common_translate(signup.language, 'signup_request_denial_reason_contact')
    ]
    message = '\n\n'.join(lines)
    community = get_community(city_customer.community_id)
    app = get_app_by_id(community.default_app)
    from_email = '%s <%s>' % (community.name, app.dashboard_email_address)
    send_mail(from_email, signup.customer_email, subject, message)


def set_customer_signup_status(city_customer, signup, approved, reason=None, send_approval_email=True):
    # type: (Customer, CustomerSignup, bool, unicode, bool) -> None
    """Set the customer signup to done and move the inbox message to trash"""

    def trans():
        to_put = [signup]
        inbox_message = None
        signup.done = True
        signup.status = CustomerSignupStatus.APPROVED if approved else CustomerSignupStatus.DENIED
        if signup.inbox_message_key:
            inbox_message = db.get(signup.inbox_message_key)
            if inbox_message:
                if approved:
                    inbox_message.trashed = True
                else:
                    inbox_message.read = True
                to_put.append(inbox_message)
        if not approved and signup.service_email:
            service_user = users.User(signup.service_email)
            sln_settings = get_solution_settings(service_user)
            sln_settings.hidden_by_city = datetime.now()
            sln_settings.updates_pending = True
            info = ServiceInfo.create_key(service_user, ServiceIdentity.DEFAULT).get()  # type: ServiceInfo
            info.visible = False
            info.put()
            # Publish to make the service invisible
            deferred.defer(common_provision, service_user, run_checks=False, _transactional=True)
            to_put.append(sln_settings)

        db.put(to_put)
        return inbox_message

    message = run_in_xg_transaction(trans)
    if message:
        service_user = signup.parent().service_user
        sln_settings = get_solution_settings(service_user)

        if approved:
            if send_approval_email:
                _send_approved_signup_email(signup)
        else:
            _send_denied_signup_email(city_customer, signup, reason)

        status_reply_message = _send_signup_status_inbox_reply(sln_settings, signup.inbox_message_key, approved, reason)
        send_signup_update_messages(sln_settings, message, status_reply_message)


def send_message_updates(sln_settings, type_, *messages):
    service_identity = ServiceIdentity.DEFAULT
    service_info = get_service_info(sln_settings.service_user, ServiceIdentity.DEFAULT)

    sm_data = [{u'type': type_}]
    for message in messages:
        message_to = SolutionInboxMessageTO.fromModel(message, sln_settings, service_info, True)
        sm_data.append({
            u'type': u'solutions.common.messaging.update',
            u'message': serialize_complex_value(message_to, SolutionInboxMessageTO, False)
        })

    channel.send_message(sln_settings.service_user, sm_data, service_identity=service_identity)


def send_signup_update_messages(sln_settings, *messages):
    # Sleep to allow datastore indexes to update
    time.sleep(2)
    send_message_updates(
        sln_settings, u'solutions.common.customer.signup.update', *messages
    )


def add_service_consent(email, type_, data):
    return update_service_consent(email, True, type_, data)


def remove_service_consent(email, type_, data):
    return update_service_consent(email, False, type_, data)


@ndb.transactional(xg=True)
def update_service_consent(email, grant, type_, data):
    updated = False
    sec_key = SolutionServiceConsent.create_key(email)
    sec = sec_key.get()
    if not sec:
        sec = SolutionServiceConsent(key=sec_key)

    if grant:
        if type_ not in sec.types:
            updated = True
            sec.types.append(type_)
            sec.put()
    elif type_ in sec.types:
        updated = True
        sec.types.remove(type_)
        sec.put()

    if updated:
        SolutionServiceConsentHistory(consent_type=type_, data=data, parent=sec_key).put()
        request_data = {
            'email': email,
            'grant': grant,
            'type': type_,
            'data': data,
        }
        log_offload.create_log(email, 'oca.service_consents', request_data, None)
    return updated
