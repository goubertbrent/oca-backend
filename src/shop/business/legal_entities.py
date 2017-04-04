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
# @@license_version:1.3@@

from types import NoneType

from rogerthat.consts import OFFICIALLY_SUPPORTED_COUNTRIES
from rogerthat.rpc.service import BusinessException
from mcfw.rpc import arguments, returns
from shop.business.i18n import CURRENCIES
from shop.exceptions import EmptyValueException
from shop.models import LegalEntity, Customer, RegioManagerTeam


@returns(LegalEntity)
@arguments(entity_id=(int, long, NoneType), name=unicode, address=unicode, postal_code=unicode, city=unicode,
           country_code=unicode, phone=unicode, email=unicode, vat_percent=(int, long), vat_number=unicode,
           currency_code=unicode, iban=unicode, bic=unicode, terms_of_use=unicode, revenue_percentage=(int, long))
def put_legal_entity(entity_id, name, address, postal_code, city, country_code, phone, email, vat_percent, vat_number,
                     currency_code, iban, bic, terms_of_use, revenue_percentage):
    fx_arguments = locals()
    for k, v in fx_arguments.items():
        if not v and k and k != 'entity_id':
            raise EmptyValueException(k)
    if country_code not in OFFICIALLY_SUPPORTED_COUNTRIES:
        raise BusinessException('Invalid country code %s ' % country_code)
    if currency_code not in CURRENCIES:
        raise BusinessException('Invalid currency %s' % currency_code)

    if entity_id is not None:
        entity = LegalEntity.get_by_id(entity_id)
        if not entity:
            raise BusinessException('Could not find legal entity with id %d' % entity_id)
    else:
        entity = LegalEntity(is_mobicage=False)
    for prop, val in fx_arguments.items():
        entity.__setattr__(prop, val)
    entity.put()
    return entity


@returns(int)
@arguments(customer=Customer, team=(NoneType, RegioManagerTeam))
def get_vat_pct(customer, team=None):
    team = team or RegioManagerTeam.get_by_id(customer.team_id)
    if team.id != customer.team_id:
        raise BusinessException('Invalid team specified to get_vat_pct, got %d, expected %d' % (team.id, customer.team_id))
    if customer.should_pay_vat:
        return team.legal_entity.vat_percent
    return 0
