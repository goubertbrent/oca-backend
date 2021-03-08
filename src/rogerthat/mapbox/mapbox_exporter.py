import json
import logging
from datetime import datetime

import requests
from google.appengine.ext import ndb
from google.appengine.ext.deferred import deferred

from rogerthat.bizz.job import run_job
from rogerthat.bizz.maps.services import get_place_details
from rogerthat.rpc import users
from rogerthat.models import OpeningHours, ServiceProfile, BaseServiceProfile, NdbServiceProfile
from rogerthat.models.settings import ServiceInfo
from rogerthat.settings import get_server_settings
from rogerthat.to.maps import OpeningHoursTO

SERVICES_PROFIT_KEY = 'cklau70dk095923o1eg2y123o'
SERVICES_NON_PROFIT_KEY = 'cklau7gvs0ye123qmrhq9h19i'
SERVICES_CITY_KEY = 'cklau7qfc0j2b21n3un69dne8'
SERVICES_EMERGENCY_KEY = 'cklau8ben1ia522jckxg8c67c'


def get_dataset_id_from_organization_type(organization_type):
    types = {
        BaseServiceProfile.ORGANIZATION_TYPE_PROFIT: SERVICES_PROFIT_KEY,
        BaseServiceProfile.ORGANIZATION_TYPE_NON_PROFIT: SERVICES_NON_PROFIT_KEY,
        BaseServiceProfile.ORGANIZATION_TYPE_CITY: SERVICES_CITY_KEY,
        BaseServiceProfile.ORGANIZATION_TYPE_EMERGENCY: SERVICES_EMERGENCY_KEY
    }
    return types.get(organization_type)


def save_to_mapbox_dataset(service_info, sections, profile, icon):
    # type: (ServiceInfo, object, ServiceProfile, object) -> None
    phone_number = ''
    if service_info.addresses:
        address = service_info.addresses[0]
        if service_info.phone_numbers:
            phone_number = str(service_info.phone_numbers[0].value)
        logging.info(address.coordinates)
        dataset_id = get_dataset_id_from_organization_type(profile.organizationType)
        geometry = {
            'type': 'Point',
            'coordinates': [address.coordinates.lon, address.coordinates.lat]
        }
        properties = {
            'id': service_info.service_user.email(),
            'icon': icon.fa_icon,
            'icon_color': icon.icon_color,
            # mapbox does not support objects as properties
            'data':  json.dumps({
                'name': service_info.name,
                'email': str(service_info.email_addresses[0].value),
                'address': {
                    'street': address.street,
                    'street_number': address.street_number,
                    'postal_code': address.postal_code,
                },
                'timezone': service_info.timezone,
                'description': service_info.description,
                'phone_number': phone_number,
                'sections': [section.to_dict() for section in sections]
            })
        }
        mapbox_feature = {
            "id": service_info.service_user.email(),
            "type": "Feature",
            "geometry": geometry,
            "properties": properties
        }
        add_features_mapbox(mapbox_feature, dataset_id)

def add_features_mapbox(feature, dataset_id):
    logging.info(feature)
    feature_id = feature['id']
    url =  'https://api.mapbox.com/datasets/v1/%s/%s/features/%s?access_token=%s' % (
        USERNAME, dataset_id, feature_id, get_server_settings().mapbox_access_token)
    logging.info('url: %s' % url)

    result = requests.put(url, json=feature)
    logging.info('status: %s content: %s' % (result.status_code, result.content))
    result.raise_for_status()


def import_all_services():
    run_job(_get_services_query, [], _save_to_mapbox, [])


def _get_services_query():
    return ServiceInfo.query()


def _save_to_mapbox(key):
    from rogerthat.bizz.maps.services import _get_map_item_details_to_from_ids
    service_email = key.parent().id()
    profile_key = NdbServiceProfile.createKey(users.User(service_email))
    keys = [key, profile_key]

    service_info,  service_profile = ndb.get_multi(keys)  # type: ServiceInfo, NdbServiceProfile
    logging.info('processing ' + service_info.name)

    results = _get_map_item_details_to_from_ids([service_email])
    icon = get_place_details(service_info.main_place_type, 'en')
    if results:
        sections = results[0].sections
        save_to_mapbox_dataset(service_info, sections, service_profile, icon)



def create_tile(tilename, dataset_Id):
    server_settings= get_server_settings()
    url = 'https://api.mapbox.com/uploads/v1/%s?access_token=%s' % (server_settings.mapbox_username, server_settings.mapbox_access_token)
    tileset = '%s.%s' % (server_settings.mapbox_username, tilename)
    bodyurl = 'mapbox://datasets/%s/%s' % (server_settings.mapbox_username, dataset_Id)

    params = {'tileset': tileset, 'url': bodyurl, 'name': tilename}

    result = requests.post(url, json=params)
    if result.status_code != 200:
        logging.info('status code: %s status content: %s', result.status_code, result.content)
        result.raise_for_status()


MAPBOX_QUEUE = 'mapbox'


def dataset_to_tileset():
    deferred.defer(create_tile, 'services_profit', SERVICES_PROFIT_KEY, _queue=MAPBOX_QUEUE)
    deferred.defer(create_tile, 'services_non_profit', SERVICES_NON_PROFIT_KEY, _queue=MAPBOX_QUEUE)
    deferred.defer(create_tile, 'services_city', SERVICES_CITY_KEY, _queue=MAPBOX_QUEUE)
    deferred.defer(create_tile, 'services_emergency', SERVICES_EMERGENCY_KEY, _queue=MAPBOX_QUEUE)
