# -*- coding: utf-8 -*-
# Copyright 2020 Green Valley NV
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
import logging

from google.appengine.ext.deferred import deferred

from rogerthat.bizz.job import run_job
from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.models.settings import ServiceInfo
from rogerthat.utils.location import _coordinates_to_address
from solutions.common.bizz import common_provision
from solutions.common.dal import get_solution_settings


def migrate_service_info_addresses(dry_run=True):
    run_job(_get_all_service_info, [], _update_service_info_addresses, [dry_run], worker_queue=MIGRATION_QUEUE)


def _get_all_service_info():
    return ServiceInfo.query()


def _update_service_info_addresses(service_info_key, dry_run=False):
    service_info = service_info_key.get()  # type: ServiceInfo
    if not service_info.addresses:
        return
    updated = False
    original_addresses = [a.to_dict() for a in service_info.addresses]
    for address in service_info.addresses:
        if address.coordinates:
            results = _coordinates_to_address(address.coordinates.lat, address.coordinates.lon).get('results', [])
            if results:
                result = results[0]
                for component in result['address_components']:
                    long_name = component['long_name']
                    short_name = component['short_name']
                    for t in component['types']:
                        if t == 'street_number':
                            address.street_number = long_name
                        elif t == 'route':
                            address.street = long_name
                        elif t == 'locality':
                            address.locality = long_name
                        elif t == 'country':
                            address.country = short_name
                        elif t == 'postal_code':
                            address.postal_code = long_name
            missing = [prop for prop in ('country', 'locality', 'postal_code', 'street', 'street_number')
                       if not getattr(address, prop)]
            if missing:
                logging.warning('Address is missing the following properties: %s\nAddress: %s\nService: %s', missing,
                                address, service_info.service_user)
            else:
                updated = True
                if 'value' in address._properties:
                    del address._properties['value']
    if updated:
        if dry_run:
            logging.info('Updating addresses\n%s\n%s', original_addresses,
                         [a.to_dict() for a in service_info.addresses])
        else:
            service_info.put()
