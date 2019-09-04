# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
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
# @@license_version:1.5@@

from mcfw.consts import MISSING
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.rpc import users
from solutions.common.bizz.discussion_groups import get_discussion_groups, put_discussion_group, delete_discussion_group
from solutions.common.to.discussion_groups import DiscussionGroupTO


@rest("/common/discussion_groups/list", "get", read_only_access=True)
@returns([DiscussionGroupTO])
@arguments()
def rest_get_discussion_groups():
    service_user = users.get_current_user()
    discussion_groups = get_discussion_groups(service_user)
    return [DiscussionGroupTO.from_model(group) for group in discussion_groups]


@rest("/common/discussion_groups", "post", read_only_access=True)
@returns(DiscussionGroupTO)
@arguments(discussion=DiscussionGroupTO)
def rest_put_discussion_group(discussion):
    service_user = users.get_current_user()
    discussion_id = None if discussion.id is MISSING else discussion.id
    discussion_group = put_discussion_group(service_user, discussion.topic, discussion.description, discussion_id)
    return DiscussionGroupTO.from_model(discussion_group)


@rest("/common/discussion_groups/delete", "post", read_only_access=True)
@returns()
@arguments(discussion_group_id=(int, long))
def rest_delete_discussion_group(discussion_group_id):
    delete_discussion_group(users.get_current_user(), discussion_group_id)
