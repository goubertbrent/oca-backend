# -*- coding: utf-8 -*-
# Copyright 2017 Mobicage NV
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

from types import NoneType

from google.appengine.api import users as gusers

from rogerthat.rpc.service import BusinessException
from mcfw.rpc import arguments
from shop.bizz import is_admin
from shop.dal import get_mobicage_legal_entity
from shop.models import Product, RegioManager


@arguments(legal_entity_id=(int, long, NoneType), google_user=gusers.User)
def list_products(legal_entity_id=None, google_user=None):
    if google_user:
        manager = RegioManager.get(RegioManager.create_key(google_user.email()))
        if manager:
            legal_entity_id = manager.team.legal_entity.key().id()
        elif is_admin(google_user):
            legal_entity_id = get_mobicage_legal_entity().key().id()
        else:
            raise BusinessException('No manager found with email %s and no ')
    elif not legal_entity_id:
        raise BusinessException('Missing argument legal_entity_id or google_user')
    return sorted(Product.list_visible_by_legal_entity(legal_entity_id), key=lambda x: x.description)
