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

from html2text import HTML2Text
from typing import Any, Dict

from mcfw.rpc import returns, arguments
from rogerthat.models import ServiceIdentity
from rogerthat.rpc import users
from rogerthat.utils.channel import send_message
from rogerthat.utils.service import create_service_identity_user


@returns(bool)
@arguments(service_identity=unicode)
def is_default_service_identity(service_identity):
    if not service_identity:
        return True
    if service_identity == ServiceIdentity.DEFAULT:
        return True
    return False


@returns(users.User)
@arguments(service_user=users.User, service_identity=unicode)
def create_service_identity_user_wo_default(service_user, service_identity):
    if is_default_service_identity(service_identity):
        return service_user
    else:
        return create_service_identity_user(service_user, service_identity)


def limit_string(string, limit):
    """
    Cuts off a string on last word instead of max chars and adds ellipsis at the end
    Args:
        string (unicode)
        limit (int)
    """
    string = string.strip()
    if len(string) > limit:
        string = string[:limit - 3]
        string = string.rsplit(' ', 1)[0] + '...'
    return string


def get_extension_for_content_type(content_type):
    return content_type.split("/")[1]


def html_to_markdown(html_content, base_url=None):
    if not html_content:
        return html_content
    converter = HTML2Text(baseurl=base_url, bodywidth=0)
    converter.ignore_images = True
    return converter.handle(html_content)


def send_client_action(service_user, action):
    # type: (users.User, Dict[str, Any]) -> None
    """This can be useful for when the server asynchronyously changes data that the client might be using"""
    send_message(service_user, 'client-action', action=action)
