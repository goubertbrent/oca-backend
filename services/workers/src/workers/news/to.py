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

from common.mcfw.properties import unicode_property, unicode_list_property, bool_property,\
    long_property
from common.to import TO


class CreateMatchesTO(TO):
    news_id = long_property('news_id')
    old_group_ids = unicode_list_property('old_group_ids')
    should_create_notification = bool_property('should_create_notification')
    
    
class DeleteMatchesTO(TO):
    news_id = long_property('news_id')


class UpdateServiceVisibilityTO(TO):
    service_identity_email = unicode_property('service_identity_email')
    visible = bool_property('visible')
    
    
class CreateUserMatchesTO(TO):
    user_id = unicode_property('user_id')
    group_ids = unicode_list_property('group_ids')
    
    
class BlockUserMatchesTO(TO):
    user_id = unicode_property('user_id')
    service_identity_email = unicode_property('service_identity_email')
    group_id = unicode_property('group_id')


class CleanupUserTO(TO):
    user_id = unicode_property('user_id')