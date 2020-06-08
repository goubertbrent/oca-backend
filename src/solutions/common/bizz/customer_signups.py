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

import json

from google.appengine.ext import db

from mcfw.rpc import arguments, returns
from rogerthat.models import Message
from rogerthat.models.properties.forms import FormResult
from rogerthat.rpc import users
from rogerthat.service.api import messaging
from rogerthat.to.messaging.forms import TextBlockFormTO, TextBlockTO, FormTO
from rogerthat.to.messaging.service_callback_results import FormAcknowledgedCallbackResultTO
from rogerthat.to.service import UserDetailsTO
from rogerthat.utils.app import get_app_user_tuple
from shop.dal import get_customer
from solutions import translate
from solutions.common.bizz import SolutionModule
from solutions.common.dal import get_solution_main_branding, get_solution_settings
from solutions.common.models import SolutionInboxMessage
from solutions.common.to.qanda import ModuleTO
from solutions.common.to.services import ModuleAndBroadcastTypesTO


def get_modules_and_broadcast_types():
    from solutions.common.bizz.service import get_allowed_modules, get_allowed_broadcast_types
    city_service_user = users.get_current_user()
    city_customer = get_customer(city_service_user)
    lang = get_solution_settings(city_service_user).main_language
    modules = [ModuleTO.fromArray([k, SolutionModule.get_translated_description(lang, k)]) for k in
               get_allowed_modules(city_customer)]
    broadcast_types = [translate(lang, k) for k in get_allowed_broadcast_types(city_customer)]
    return ModuleAndBroadcastTypesTO(modules, broadcast_types)


def rest_signup_get_modules_and_broadcast_types(signup_key):
    modules_and_broadcast_types = get_modules_and_broadcast_types()
    preselected_modules = []

    signup = db.get(signup_key)
    if signup:
        preselected_modules = signup.modules

    if preselected_modules:
        for module in modules_and_broadcast_types.modules:
            module.is_default = module.key in preselected_modules

    return modules_and_broadcast_types


@arguments(service_user=users.User, service_identity=unicode, message_key=unicode, app_user=users.User, name=unicode,
           answer_id=unicode, parent_inbox_message=SolutionInboxMessage)
def process_updated_customer_signup_message(service_user, service_identity, message_key, app_user, name, answer_id,
                                            parent_inbox_message):
    # type: (users.User, unicode, unicode, users.User, unicode, unicode, SolutionInboxMessage) -> None
    from solutions.common.bizz.messaging import MESSAGE_TAG_DENY_SIGNUP
    from solutions.common.restapi.services import rest_create_service_from_signup
    with users.set_user(service_user):
        sln_settings = get_solution_settings(service_user)
        if answer_id == 'decline':
            widget = TextBlockTO()
            widget.max_chars = 1024
            form = TextBlockFormTO()
            form.type = TextBlockTO.TYPE
            form.widget = widget
            form.positive_button = translate(sln_settings.main_language, 'Confirm')
            form.negative_button = translate(sln_settings.main_language, 'Cancel')
            form.javascript_validation = """function run(result) {
        return result.value ? true : '%s';
    }""" % translate(sln_settings.main_language, 'this_field_is_required', _duplicate_backslashes=True)
            human_user, app_id = get_app_user_tuple(app_user)
            messaging.send_form(parent_key=parent_inbox_message.message_key,
                                parent_message_key=parent_inbox_message.message_key,
                                message=translate(sln_settings.main_language, 'signup_not_ok'),
                                member=human_user.email(),
                                app_id=app_id,
                                flags=Message.FLAG_AUTO_LOCK,
                                branding=get_solution_main_branding(service_user).branding_key,
                                tag=json.dumps({'__rt__.tag': MESSAGE_TAG_DENY_SIGNUP,
                                                'signup_key': parent_inbox_message.category_key}),
                                form=form,
                                service_identity=service_identity,
                                alert_flags=Message.ALERT_FLAG_VIBRATE)
        elif answer_id == 'approve':
            modules_and_broadcast_types = rest_signup_get_modules_and_broadcast_types(parent_inbox_message.category_key)
            modules = [m.key for m in modules_and_broadcast_types.modules if m.is_default]
            result = rest_create_service_from_signup(parent_inbox_message.category_key, modules,
                                                     broadcast_types=modules_and_broadcast_types.broadcast_types,
                                                     force=True)  # type: CreateServiceStatusTO
            if not result.success:
                messaging.send(parent_message_key=message_key,
                               message=result.errormsg,
                               answers=[],
                               flags=Message.FLAG_ALLOW_DISMISS,
                               branding=get_solution_main_branding(service_user).branding_key,
                               tag=None,
                               service_identity=service_identity)


@returns(FormAcknowledgedCallbackResultTO)
@arguments(service_user=users.User, status=int, form_result=FormResult, answer_id=unicode, member=unicode,
           message_key=unicode, tag=unicode, received_timestamp=int, acked_timestamp=int, parent_message_key=unicode,
           result_key=unicode, service_identity=unicode, user_details=[UserDetailsTO])
def deny_signup(service_user, status, form_result, answer_id, member, message_key, tag,
                received_timestamp, acked_timestamp, parent_message_key, result_key,
                service_identity, user_details):
    from solutions.common.restapi import rest_customer_signup_reply
    with users.set_user(service_user):
        if answer_id == FormTO.POSITIVE:
            tag_dict = json.loads(tag)
            rest_customer_signup_reply(tag_dict['signup_key'], form_result.result.value)
