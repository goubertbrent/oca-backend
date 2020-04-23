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

from rogerthat.bizz.job import run_job
from rogerthat.consts import MIGRATION_QUEUE, DEBUG
from rogerthat.models.settings import ServiceInfo
from rogerthat.utils.location import _coordinates_to_address, geo_code
from solutions.common.dal import get_solution_settings


def migrate_service_info_addresses(dry_run=True):
    run_job(_get_all_service_info, [], _update_service_info_addresses, [dry_run], worker_queue=MIGRATION_QUEUE)


def _get_all_service_info():
    return ServiceInfo.query()


def _get_address_from_result(result):
    all_properties = ['country', 'locality', 'postal_code', 'street', 'street_number']
    d = {}
    for component in result['address_components']:
        for t in component['types']:
            if t == 'street_number':
                prop = 'street_number'
                d[prop] = component['long_name']
                all_properties.remove(prop)
            elif t == 'route':
                prop = 'street'
                d[prop] = component['long_name']
                all_properties.remove(prop)
            elif t == 'locality':
                prop = 'locality'
                d[prop] = component['long_name']
                all_properties.remove(prop)
            elif t == 'country':
                prop = 'country'
                d[prop] = component['short_name']
                all_properties.remove(prop)
            elif t == 'postal_code':
                prop = 'postal_code'
                d[prop] = component['long_name']
                all_properties.remove(prop)
    return all_properties, d


def _update_service_info_addresses(service_info_key, dry_run=False):
    service_info = service_info_key.get()  # type: ServiceInfo
    if not service_info.addresses:
        return
    
#     sln_settings = get_solution_settings(service_info.service_user)
#     if sln_settings.service_disabled:
#         service_info_key.delete()
#         return
    
    updated = False
    original_addresses = [a.to_dict() for a in service_info.addresses]
    for address in service_info.addresses:
        if DEBUG:
            value = address.get_address_line('nl')
        else:
            value = address.value

        if not value and not address.coordinates:
            logging.warn('_update_service_info_addresses missing value and coords')
            continue
        
        address_updated = False
        if value:
            try:
                result = geo_code(value)
            except:
                result = None
                logging.warn('_update_service_info_addresses geocode zero results')
            
            if result:
                missing_properties_value, result_value = _get_address_from_result(result)
                if missing_properties_value:
                    logging.warn('_update_service_info_addresses geocode missing: %s -> %s', missing_properties_value, result_value)
                else:
                    address.street_number = result_value['street_number']
                    address.street = result_value['street']
                    address.locality = result_value['locality']
                    address.country = result_value['country']
                    address.postal_code = result_value['postal_code']
                    address_updated = True
            
        
        if not updated and address.coordinates:
            results = _coordinates_to_address(address.coordinates.lat, address.coordinates.lon).get('results', [])
            if results:
                missing_properties_coords, result_coords = _get_address_from_result(results[0])
                if missing_properties_coords:
                    logging.warn('_update_service_info_addresses latlon missing: %s -> %s', missing_properties_coords, result_coords)
                else:
                    address.street_number = result_coords['street_number']
                    address.street = result_coords['street']
                    address.locality = result_coords['locality']
                    address.country = result_coords['country']
                    address.postal_code = result_coords['postal_code']
                    address_updated = True
        
        if address_updated:
            updated = True
#             if 'value' in address._properties:
#                 del address._properties['value']
        else:
            logging.warn('_update_service_info_addresses address not updated\nAddress: %s\nService: %s', address, service_info.service_user)
    
    if updated:
        if dry_run:
            logging.info('Updating addresses\n%s\n%s', original_addresses, [a.to_dict() for a in service_info.addresses])
        else:
            service_info.put()
