# -*- coding: utf-8 -*-
# Copyright 2017 GIG Technology NV
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
# @@license_version:1.2@@

from rogerthat.models import ServiceProfile
from rogerthat.rpc.solutions import service_api_callback_handler
from solutions.common.api_callback_handlers import common_friend_invited, common_messaging_flow_member_result, \
    common_system_api_call, common_messaging_form_update, common_messaging_update, common_messaging_poke, \
    common_friend_invite_result, common_friend_register, common_friend_register_result, common_new_chat_message, \
    common_chat_deleted
from solutions.flex import SOLUTION_FLEX


def wrap_common_callback_handler(f, code):
    return service_api_callback_handler(solution=SOLUTION_FLEX, code=code)(f)

friend_invited = wrap_common_callback_handler(common_friend_invited,
                                              ServiceProfile.CALLBACK_FRIEND_INVITED)

messaging_poke = wrap_common_callback_handler(common_messaging_poke,
                                              ServiceProfile.CALLBACK_MESSAGING_POKE)

messaging_flow_member_result = wrap_common_callback_handler(common_messaging_flow_member_result,
                                                            ServiceProfile.CALLBACK_MESSAGING_FLOW_MEMBER_RESULT)

system_api_call = wrap_common_callback_handler(common_system_api_call,
                                               ServiceProfile.CALLBACK_SYSTEM_API_CALL)

messaging_update = wrap_common_callback_handler(common_messaging_update,
                                                ServiceProfile.CALLBACK_MESSAGING_ACKNOWLEDGED)

messaging_form_update = wrap_common_callback_handler(common_messaging_form_update,
                                                     ServiceProfile.CALLBACK_MESSAGING_FORM_ACKNOWLEDGED)

friend_invite_result = wrap_common_callback_handler(common_friend_invite_result,
                                                    ServiceProfile.CALLBACK_FRIEND_INVITE_RESULT)

friend_register = wrap_common_callback_handler(common_friend_register,
                                               ServiceProfile.CALLBACK_FRIEND_REGISTER)

friend_register_result = wrap_common_callback_handler(common_friend_register_result,
                                                      ServiceProfile.CALLBACK_FRIEND_REGISTER_RESULT)

new_chat_message = wrap_common_callback_handler(common_new_chat_message,
                                                ServiceProfile.CALLBACK_MESSAGING_NEW_CHAT_MESSAGE)

messaging_chat_deleted = wrap_common_callback_handler(common_chat_deleted,
                                                      ServiceProfile.CALLBACK_MESSAGING_CHAT_DELETED)
