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


import logging

from rogerthat.bizz.job import run_job
from rogerthat.consts import MIGRATION_QUEUE
from rogerthat.models.settings import ServiceInfo


MAPPING = {
    'accounting': 'accounting_firm',
    'association': None,
    'bus_station': None,
    'butcher': 'butcher_shop',
    'car_rental': 'car_rental_agency',
    'courthouse': 'city_courthouse',
    'grocery_or_supermarket': 'supermarket',
    'hair_care': 'hair_salon',
    'light_rail_station': None,
    'lodging': 'hotel',
    'movie_rental': 'movie_rental_store',
    'nurse': 'registered_general_nurse',
    'parking': 'parking_lot',
    'police': 'civil_police',
    'secondary_school': None,
    'shopping_mall': 'shopping_center',
    'storage': 'storage_facility',
    'subway_station': None,
    'train_station': 'train_depot',
    'transit_station': 'transit_depot',
    'veterinary_care': 'veterinarian',
}


def migrate_place_types(dry_run=True):
    run_job(_get_all_service_info, [], _update_service_info_places, [dry_run], worker_queue=MIGRATION_QUEUE)


def _get_all_service_info():    
    return ServiceInfo.query()


def _update_service_info_places(service_info_key, dry_run=False):
    service_info = service_info_key.get()  # type: ServiceInfo
    if not service_info.main_place_type:
        return
    if not service_info.place_types:
        return

    logging.debug('_update_service_info_places service:%s main:%s types:%s', service_info.service_user, service_info.main_place_type, service_info.place_types)
    
    updated = False
    manual_update_needed = False
    missing_keys = MAPPING.keys()
    
    if service_info.main_place_type in missing_keys:
        new_main_place_type = MAPPING.get(service_info.main_place_type)
        if new_main_place_type:
            updated = True
            service_info.main_place_type = new_main_place_type
        else:
            manual_update_needed = True
    
    new_place_types = []
    updated_place_types = False

    for place_type in service_info.place_types:
        if place_type not in missing_keys:
            new_place_types.append(place_type)
            continue
        updated_place_types = True
        new_place_type = MAPPING.get(place_type)
        if new_place_type:
            new_place_types.append(new_place_type)
        else:
            manual_update_needed = True
        
    if updated_place_types:
        updated = True
        service_info.place_types = new_place_types
    
    if manual_update_needed:
        logging.warn('_update_service_info_places manual update needed for service:%s', service_info.service_user)
            
    elif updated and not dry_run:
        service_info.put()
    
