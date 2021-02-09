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
from __future__ import unicode_literals

import json
import logging
import urlparse

import cloudstorage
from google.appengine.ext import ndb, db
from google.appengine.ext.ndb.key import Key
from google.appengine.ext.ndb.model import GeoPt
from typing import Dict, List, Tuple

from oca_imaging import generate_scaled_images
from rogerthat.bizz.job import run_job
from rogerthat.bizz.maps.poi.models import POILocation, PointOfInterest, POIStatus
from rogerthat.consts import MIGRATION_QUEUE, DEBUG, MIGRATION_QUEUE2, OFFLOAD_QUEUE
from rogerthat.dal import parent_ndb_key
from rogerthat.models import NdbModel, ServiceIdentity, OpeningHours, OpeningPeriod, OpeningHour
from rogerthat.models.news import MediaType
from rogerthat.models.settings import ServiceLocation, MediaItem
from rogerthat.models.utils import ndb_allocate_ids
from rogerthat.rpc import users
from rogerthat.utils.cloud_tasks import create_task, schedule_tasks
from shop.bizz import create_customer_service_to
from shop.models import CustomerSignup, Customer
from solutions import SOLUTION_COMMON
from solutions.common.bizz import OrganizationType, SolutionModule
from solutions.common.bizz.images import get_image_requests_for_file, _get_scaled_images, \
    set_scaled_images_from_uploaded_files
from solutions.common.bizz.opening_hours import get_opening_hours
from solutions.common.bizz.service import create_customer_with_service, put_customer_service
from solutions.common.bizz.settings import get_service_info
from solutions.common.consts import OCA_FILES_BUCKET
from solutions.common.models import SolutionBrandingSettings
from solutions.common.models.forms import UploadedFile


class BoomPOI(NdbModel):
    service_email = ndb.StringProperty()  # set when imported as service
    poi_id = ndb.IntegerProperty()  # set when imported as POI
    data = ndb.JsonProperty()
    media_mapping = ndb.JsonProperty()  # key: relative file path on disk, value: urlsafe ndb key

    @classmethod
    def create_key(cls, id):
        return ndb.Key(cls, id)


GEMEENTE_BOOM_POI_ID = 10

BOOM_POI_CATEGORIES = {
    # 'admin.entities.pointOfInterestCategory.enums.RESTAURANTS'
    3: 'restaurant',
    # 'admin.entities.pointOfInterestCategory.enums.FASHION'
    6: None,
    # 'admin.entities.pointOfInterestCategory.enums.LEISURE'
    7: 'leisurecentre',
    # 'admin.entities.pointOfInterestCategory.enums.FOOD_CATERING'
    8: 'catering_service',
    # 'admin.entities.pointOfInterestCategory.enums.SERVICES'
    13: None,
    # 'admin.entities.pointOfInterestCategory.enums.HEALTH'
    15: None,
    # 'admin.entities.pointOfInterestCategory.enums.GENERAL_STORE'
    16: 'supermarket',
    # 'admin.entities.pointOfInterestCategory.enums.DETAIL_STORE'
    17: None
}


class BoomTheme(object):
    NONE = 0
    # museum, church, culture centrum, street, market
    CULTURE = 1
    # stadion, park, tennis course, tomorrowland, hockeyclub, ...
    SPORT = 2
    SHOPPING = 3
    RESIDENTIAL_AREA = 4
    SCHOOLS = 5


@staticmethod
def _patched_is_file_accessible(filename, for_write=False):
    from google.appengine.tools.devappserver2.python.runtime.stubs import FakeFile
    return FakeFile.Visibility.OK


def _get_data(file_path):
    if DEBUG:
        from google.appengine.tools.devappserver2.python.runtime.stubs import FakeFile
        FakeFile.is_file_accessible = _patched_is_file_accessible
        with open(file_path) as f:
            return json.load(f)
    else:
        with cloudstorage.open(file_path) as f:
            return json.load(f)


def one_import_pois(city_customer, file_path):
    # type: (Customer, str) -> None
    data = _get_data(file_path)
    pois = data['pois']
    to_put = []
    for service in pois:
        model = BoomPOI(key=BoomPOI.create_key(service['id']), data=service)
        if service['id'] == GEMEENTE_BOOM_POI_ID:
            # Don't create new service for gemeente
            model.service_email = city_customer.service_email
        to_put.append(model)
    ndb.put_multi(to_put)


def two_create_services_and_pois(city_customer):
    keys = BoomPOI.query().fetch(keys_only=True)
    schedule_tasks([create_task(create_service_or_poi, key, city_customer) for key in keys],
                   queue_name=MIGRATION_QUEUE)


def test_1_create(city_customer, poi_key):
    create_service_or_poi(poi_key, city_customer)


def test_2_import_media(poi_key):
    return _populate_service_info(poi_key)


def three_import_service_media():
    # Do not run before all POI's/services are imported
    run_job(_get_all_models, [], _populate_service_info, [], controller_queue=MIGRATION_QUEUE,
            worker_queue=MIGRATION_QUEUE2)


def _get_all_models():
    return BoomPOI.query()


def four_create_scaled_images():
    run_job(_get_all_models, [], _created_scaled_images, [], worker_queue=OFFLOAD_QUEUE)


def five_import_storylines(file_path):
    data = _get_data(file_path)
    storylines = data['storylines']
    # TODO
    raise NotImplementedError()


def create_service_or_poi(key, city_customer):
    # type: (Key, Customer) -> BoomPOI
    model = key.get()  # type: BoomPOI
    if model.service_email or model.poi_id:
        logging.debug('POI/service already imported as %s', model.service_email or model.poi_id)
        return model
    data = model.data
    company_name = data['name'][:50]
    email = data['email']
    locale = 'nl'
    phone = data['phone_number']
    if data['theme'] == BoomTheme.SHOPPING and data['email']:  # 331 out of 412
        # Create service
        logging.debug('Creating service %s', data['name'])
        modules = [m for m in CustomerSignup.DEFAULT_MODULES if m != SolutionModule.WHEN_WHERE]
        organization_type = OrganizationType.PROFIT
        service = create_customer_service_to(company_name, email, locale, phone, organization_type,
                                             city_customer.community_id, modules)

        customer = create_customer_with_service(
            city_customer=city_customer, customer=None, service=service, name=company_name, address1=data['address'],
            address2=None, zip_code=str(data['postal_code']),
            city=data['municipality'], language=locale, organization_type=organization_type,
            vat=None, website=data['url'], facebook_page=None, force=False)[0]
        result = put_customer_service(customer, service, search_enabled=False,
                                      skip_email_check=True, rollback=True, send_login_information=False)
        model.service_email = result.login
    else:
        address = _get_address(data)
        location = POILocation(
            coordinates=GeoPt(data['latitude'], data['longitude']),
            google_maps_place_id=address.google_maps_place_id,
            country=address.country,
            locality=address.locality,
            postal_code=address.postal_code,
            street=address.street,
            street_number=address.street_number,
            timezone='Europe/Brussels',
        )
        if data['opening_periods']:
            opening_hours = OpeningHours(
                type=OpeningHours.TYPE_STRUCTURED,
                periods=[OpeningPeriod(open=OpeningHour(**period['open']),
                                       close=OpeningHour(**period['close']))
                         for period in data['opening_periods']]
            )
        else:
            opening_hours = OpeningHours(type=OpeningHours.TYPE_NOT_RELEVANT)
        poi = PointOfInterest(
            community_id=city_customer.community_id,
            title=data['name'],
            description=data['description'],
            location=location,
            opening_hours=opening_hours,
            media=[],
            visible=True,
        )
        poi.status = POIStatus.VISIBLE if poi.has_complete_info else POIStatus.INCOMPLETE
        poi.put()
        model.poi_id = poi.id
    model.put()
    return model


def _populate_service_info(key):
    model = key.get()  # type: BoomPOI
    data = model.data
    if model.service_email:
        service_user = users.User(model.service_email)
        service_info = get_service_info(service_user, ServiceIdentity.DEFAULT)
        if data['description']:
            service_info.description = data['description']
        address = _get_address(data)
        to_put = [model, service_info]
        if address:
            service_info.addresses = [address]
        place_type = BOOM_POI_CATEGORIES.get(data.get('category_id'))
        if place_type:
            service_info.main_place_type = place_type
            service_info.place_types = [place_type]
        opening_hours = get_opening_hours(service_user, ServiceIdentity.DEFAULT)
        if data['opening_periods']:
            opening_hours.type = OpeningHours.TYPE_STRUCTURED
            opening_hours.periods = [OpeningPeriod(open=OpeningHour(**period['open']),
                                                   close=OpeningHour(**period['close']))
                                     for period in data['opening_periods']]
        else:
            opening_hours.type = OpeningHours.TYPE_NOT_RELEVANT
        to_put.append(opening_hours)
        media_list = data['media_items']
        if media_list:
            models, media_mapping = _get_media(model, media_list)
            logging.debug('Media for service %s: %s', service_user, models)
            if data['id'] == GEMEENTE_BOOM_POI_ID:
                service_info.media.extend([MediaItem.from_file_model(file_model) for file_model in models])
            else:
                service_info.media = [MediaItem.from_file_model(m) for m in models]
            if service_info.media:
                # Set cover photo to the first media item that is an image
                key = SolutionBrandingSettings.create_key(service_user)
                branding_settings = db.get(key)  # type: SolutionBrandingSettings
                if not branding_settings.logo_url:
                    for item in service_info.media:
                        if item.type == MediaType.IMAGE:
                            branding_settings.logo_url = item.content
                            branding_settings.put()
                            break
            to_put.extend(models)
            model.media_mapping = media_mapping
    else:
        poi = PointOfInterest.create_key(model.poi_id).get()  # type: PointOfInterest
        if poi.media:
            logging.debug('Already imported media for POI %s', model)
            return
        models, media_mapping = _get_media(model, data['media_items'])
        model.media_mapping = media_mapping
        poi.media = [MediaItem.from_file_model(file_model) for file_model in models]
        logging.debug('Media for poi %s: %s', model.poi_id, poi.media)
        to_put = [model, poi] + models
    ndb.put_multi(to_put)
    return to_put


def _get_media(poi, media_list):
    # type: (BoomPOI, List[dict]) -> Tuple[List[UploadedFile], Dict[str, str]]
    media_mapping = {}
    if not media_list:
        return [], media_mapping
    models = []
    if poi.service_email:
        parent_key = parent_ndb_key(users.User(poi.service_email), SOLUTION_COMMON)
    elif poi.poi_id:
        parent_key = PointOfInterest.create_key(poi.poi_id)
    file_ids = ndb_allocate_ids(UploadedFile, len(media_list), parent_key)
    for media, file_id in zip(media_list, file_ids):
        url = media['relative_url']  # type: str
        extension = '.' + url.rsplit('.', 1)[1]
        if poi.service_email:
            base = '/%(bucket)s/services/%(service)s/media' % {'bucket': OCA_FILES_BUCKET, 'service': poi.service_email}
            cloudstorage_path = '%(base)s/%(file_id)d%(extension)s' % {
                'base': base,
                'file_id': file_id,
                'extension': extension
            }
            key = UploadedFile.create_key_service(users.User(poi.service_email), file_id)  # type: Key
        else:
            base = '/%(bucket)s/poi/%(poi_id)d/media' % {'bucket': OCA_FILES_BUCKET, 'poi_id': poi.poi_id}
            cloudstorage_path = '%(base)s/%(file_id)d%(extension)s' % {
                'base': base,
                'file_id': file_id,
                'extension': extension
            }
            key = UploadedFile.create_key_poi(parent_key, file_id)  # type: Key
        if media['type'] == 'image':
            if extension == '.png':
                content_type = 'image/png'
            else:
                content_type = 'image/jpeg'
        else:
            raise Exception('Unsupported media type: %s' % media['type'])
        file_model = UploadedFile(key=key,
                                  content_type=content_type,
                                  title=media['title'],
                                  cloudstorage_path=cloudstorage_path,
                                  type=_get_media_type(media))
        media_mapping[media['relative_url']] = key.urlsafe()
        models.append(file_model)
    return models, media_mapping


def _get_media_type(media):
    if media['type'] == 'image':
        if media['is360']:
            return MediaType.IMAGE_360
        else:
            return MediaType.IMAGE
    elif media['type'] == 'video':
        if media['is360']:
            raise NotImplementedError()
        else:
            raise NotImplementedError()


def _get_address(data):
    # type: (dict) -> ServiceLocation
    address = ServiceLocation()
    address.name = data['name']
    address.country = 'BE'
    address.locality = data['municipality']
    address.postal_code = str(data['postal_code'])
    address.street = data['address']
    address.street_number = data['house_number']
    if address.street_number == 'z/n':
        address.street_number = None
    route_desc_url = data['route_description_url']  # type: str
    address.google_maps_place_id = None
    if route_desc_url:
        parsed_route_url = urlparse.urlparse(route_desc_url)
        parsed_query = urlparse.parse_qs(parsed_route_url.query)
        destination_place_ids = parsed_query.get('destination_place_id')
        if destination_place_ids:
            address.google_maps_place_id = destination_place_ids[0]
    address.coordinates = ndb.GeoPt(data['latitude'], data['longitude'])
    return address


def get_file_paths_to_upload():
    mapping = {}
    boom_pois = BoomPOI.query().fetch(None)
    to_get = []
    for boom_poi in boom_pois:  # type: BoomPOI
        if not boom_poi.media_mapping:
            continue
        for key_str in boom_poi.media_mapping.itervalues():
            to_get.append(Key(urlsafe=key_str))
    models = {m.key.urlsafe(): m for m in ndb.get_multi(to_get)}  # type: Dict[str, UploadedFile]
    for boom_poi in boom_pois:
        if not boom_poi.media_mapping:
            continue
        for relative_path, key_str in boom_poi.media_mapping.iteritems():
            mapping[relative_path] = models[key_str].to_dict(
                include=['id', 'content_type', 'thumbnail_path', 'cloudstorage_path']
            )
    return mapping


def _created_scaled_images(key):
    model = key.get()  # type: BoomPOI
    if model.poi_id:
        qry = UploadedFile.list_by_poi(PointOfInterest.create_key(model.poi_id))
    elif model.service_email:
        qry = UploadedFile.list_by_user(users.User(model.service_email))
    else:
        return None
    to_put = []
    for uploaded_file in qry:  # type: UploadedFile
        requests = get_image_requests_for_file(uploaded_file)
        results = generate_scaled_images(uploaded_file.original_url, requests)
        uploaded_file.scaled_images = _get_scaled_images(requests, results)
        to_put.append(uploaded_file)
    ndb.put_multi(to_put)
    if to_put:
        parent_key = to_put[0].key.parent()
        set_scaled_images_from_uploaded_files(to_put, parent_key)
