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
from collections import OrderedDict
import json
import logging
from urllib import urlencode

from google.appengine.api import urlfetch
from google.appengine.ext import db, ndb, deferred
from google.appengine.ext.ndb import GeoPt
from typing import Union, Optional

from rogerthat.bizz.job import run_job, MODE_BATCH
from rogerthat.bizz.maps.services import PLACE_DETAILS
from rogerthat.bizz.maps.services.place_types import PlaceType
from rogerthat.consts import DEBUG, MIGRATION_QUEUE
from rogerthat.models import ServiceIdentity, OpeningHours, OpeningPeriod, OpeningHour
from rogerthat.models.maps import MapServiceMediaItem
from rogerthat.models.news import MediaType
from rogerthat.models.settings import SyncedNameValue, ServiceAddress, ServiceInfo
from rogerthat.rpc import users
from rogerthat.settings import get_server_settings
from rogerthat.to.news import BaseMediaTO
from shop.dal import get_customer
from solutions import translate, SOLUTION_COMMON
from solutions.common.bizz import get_default_cover_media
from solutions.common.bizz.settings import parse_facebook_url, validate_url
from solutions.common.models import SolutionSettings, SolutionBrandingSettings, SolutionIdentitySettings
from solutions.common.models.forms import UploadedFile
from solutions.common.models.news import CityAppLocations
from solutions.common.dal import get_solution_settings


def migrate_1_uploaded_files():
    run_job(_get_all_uploaded_files, [], _put_files, [], mode=MODE_BATCH, batch_size=50, worker_queue=MIGRATION_QUEUE)


def _get_all_uploaded_files():
    return UploadedFile.query()


def _put_files(keys):
    models = ndb.get_multi(keys)
    ndb.put_multi(models)


def migrate_2_solution_settings(dry_run=True):
    run_job(_get_all_solution_settings, [], _try_create_service_info if dry_run else _create_service_info_parent, [], worker_queue=MIGRATION_QUEUE)


def _get_all_solution_settings():
    return SolutionSettings.all(keys_only=True)


def _try_create_service_info(sln_settings_key):
    try:
        sln_settings, models = _create_service_info_parent(sln_settings_key, True)
        if sln_settings:
            logging.info(db.to_dict(sln_settings))
        for model in models:
            logging.info(model)
    except Exception as e:
        logging.exception(e.message, _suppress=False)


def _create_service_info_parent(sln_settings_key, dry_run=False):
    sln_settings = db.get(sln_settings_key)  # type: SolutionSettings
    if sln_settings.service_disabled:
        logging.debug('_create_service_info disabled')
        return None, []
    for service_identity in sln_settings.identities:
        sln_i_settings_key = SolutionIdentitySettings.create_key(sln_settings.service_user, service_identity)
        deferred.defer(_create_service_info, sln_i_settings_key, dry_run=dry_run, _queue=MIGRATION_QUEUE)
    return _create_service_info(sln_settings_key, dry_run=dry_run)


def _create_service_info(sln_settings_key, dry_run=False):
    sln_settings = db.get(sln_settings_key)  # type: Union[SolutionSettings, SolutionIdentitySettings]
    branding_settings = db.get(
        SolutionBrandingSettings.create_key(sln_settings.service_user))  # type: SolutionBrandingSettings
    customer = get_customer(sln_settings.service_user)
    if not customer:
        logging.warn('_create_service_info customer not found')
        return None, []
    service_user = sln_settings.service_user
    info = ServiceInfo(key=ServiceInfo.create_key(sln_settings.service_user, ServiceIdentity.DEFAULT))

    to_put = [info]

    info.name = sln_settings.name
    info.description = sln_settings.description
    if isinstance(sln_settings, SolutionSettings):
        info.currency = sln_settings.currency
        info.timezone = sln_settings.timezone
        info.visible = sln_settings.search_enabled
        main_language = sln_settings.main_language
    else:
        root_sln_settings = get_solution_settings(sln_settings.service_user)
        info.currency = root_sln_settings.currency
        info.timezone = root_sln_settings.timezone
        info.visible = root_sln_settings.search_enabled
        main_language = root_sln_settings.main_language
        
    info.keywords = [k.strip() for k in sln_settings.search_keywords.split(' ') if k.strip()] if sln_settings.search_keywords else []
    info.addresses = []
    sln_settings.address = sln_settings.address.strip()
    place_search_keywords = [sln_settings.name]
    if sln_settings.location and sln_settings.address:
        # Search very close to the coordinates
        coordinates = [sln_settings.location.lat, sln_settings.location.lon]
        radius = 500
        logging.debug('_create_service_info search with address')
        place_search_keywords.append(' '.join(sln_settings.address.split('\n')))
        place_type = _guess_place_type_from_name(customer.name)
        logging.debug('_create_service_info search place_type: %s', place_type)
        google_place = _get_google_place_from_coordinates_and_name(place_search_keywords, coordinates, radius, place_type,
                                                                   main_language)
        if not google_place:
            logging.debug('_create_service_info search without address')
            google_place = _get_google_place_from_coordinates_and_name([sln_settings.name], coordinates, radius, place_type,
                                                                       main_language)
    else:
        place_type = None
        google_place = None
    
    if google_place:
        _fill_info_from_google_place(info, google_place)
        opening_hours = _get_opening_hours_from_google_place(google_place, service_user, sln_settings)
        if opening_hours:
            to_put.append(opening_hours)
    else:
        logging.warning('_create_service_info google place not found for service %s - %s', sln_settings.name, sln_settings.address)
        if sln_settings.address:
            address = ServiceAddress()
            address.value = sln_settings.address
            if sln_settings.location:
                address.coordinates = GeoPt(sln_settings.location.lat, sln_settings.location.lon)
            info.addresses.append(address)
    if info.place_types:
        info.main_place_type = info.place_types[0]

    if sln_settings.phone_number:
        info.phone_numbers.append(SyncedNameValue.from_value(sln_settings.phone_number))
    elif google_place and google_place.get('formatted_phone_number'):
        info.phone_numbers.append(SyncedNameValue.from_value(google_place['formatted_phone_number']))
    if not info.websites and customer.website:
        website_url = validate_url(customer.website)
        if website_url:
            logging.debug('_create_service_info website_url: %s', website_url)
            website = SyncedNameValue()
            website.value = website_url
            info.websites.append(website)
    if customer.facebook_page:
        website_urls = [w.value for w in info.websites] if info.websites else []
        if 'facebook.com' not in website_urls:
            fb_url = parse_facebook_url(customer.facebook_page)
            if fb_url:
                logging.debug('_create_service_info fb_url: %s', fb_url)
                facebook_page = SyncedNameValue()
                facebook_page.name = translate(main_language, SOLUTION_COMMON, 'Facebook page')
                facebook_page.value = fb_url
                info.websites.append(facebook_page)
    if sln_settings.qualified_identifier:
        info.email_addresses.append(SyncedNameValue.from_value(sln_settings.qualified_identifier))
    if branding_settings and branding_settings.logo_url:
        cover_photo_item = MapServiceMediaItem()
        cover_photo_item.item = BaseMediaTO()
        cover_photo_item.item.type = MediaType.IMAGE
        cover_photo_item.item.content = branding_settings.logo_url
        info.cover_media = [cover_photo_item]
    else:
        info.cover_media = get_default_cover_media(customer.organization_type)

    if not dry_run:
        ndb.put_multi(to_put)
    return sln_settings, to_put


def _get_opening_hours_from_google_place(google_place, service_user, sln_settings):
    # type: (dict, users.User, SolutionSettings) -> Optional[OpeningHours]
    if not google_place.get('opening_hours'):
        return None
    if isinstance(sln_settings, SolutionSettings):
        opening_hours_key = OpeningHours.create_key(service_user, ServiceIdentity.DEFAULT)
    else:
        opening_hours_key = OpeningHours.create_key(service_user, sln_settings.service_identity)
    opening_hours = OpeningHours(key=opening_hours_key)
    opening_hours.type = OpeningHours.TYPE_STRUCTURED
    for p in google_place['opening_hours']['periods']:
        period = OpeningPeriod()
        period.open = OpeningHour()
        period.open.day = p['open']['day']
        period.open.time = p['open']['time']
        if p.get('close'):
            # Open 24 hours when not present
            period.close = OpeningHour()
            period.close.day = p['close']['day']
            period.close.time = p['close']['time']
        opening_hours.periods.append(period)
    if opening_hours.periods:
        return opening_hours
    return None


def _guess_place_type_from_name(name):
    terms = OrderedDict()
    terms[PlaceType.SCHOOL] = ('Basisschool', 'Gemeenteschool',)
    terms[PlaceType.BAKERY] = ('Bakkerij', 'Bakery', 'Brood', 'Patisserie')
    terms[PlaceType.RESTAURANT] = ('Frituur', 'Friethuisje', 'Taverne', 'Restaurant', 'Lunch', 'Bistro', 'Brasserie')
#         'food': ('Slagerij', 'Keurslager' , 'Traiteur', 'Catering',),
    terms[PlaceType.BAR] = (u'Café', 'Cafe')
    terms[PlaceType.LIBRARY] = ('Bibliotheek',)
    terms[PlaceType.SUPERMARKET] = ('Boodschappen', 'Kruidenierswinkel', 'Supermarkt', 'Delhaize')
    terms[PlaceType.PHARMACY] = ('Apotheek',)
    terms[PlaceType.BANK] = ('Argenta', 'AXA Bank', 'AXA kantoor', 'Belfius',)
    terms[PlaceType.HAIR_CARE] = ('Coiffure', 'Hairstudio', 'Hairsalon', 'Hairstyle', 'Hairstyling', 'Kapsalon', 'Kapper',)
    terms[PlaceType.HOSPITAL] = ('AZ Herentals', 'Ziekenhuis',)
    terms[PlaceType.LAWYER] = ('Advocaat', 'Advocaten',)
    terms[PlaceType.FLORIST] = ('Bloemen',)
    terms[PlaceType.VETERINARY_CARE] = ('Dierenarts',)
    terms[PlaceType.JEWELRY_STORE] = ('Juwelen', 'Juwelier', 'Juweelontwerp',)
    terms[PlaceType.SHOE_STORE] = ('schoenen',)
    terms[PlaceType.CLOTHING_STORE] = ('Lingerie',)
    terms[PlaceType.FUNERAL_HOME] = ('Uitvaartcentrum', 'Uitvaartverzorging', 'Uitvaartzorg',)
    terms[PlaceType.INSURANCE_AGENCY] = ('Verzekeringen', 'Verzekerings',)
    terms[PlaceType.CITY_HALL] = ('Gemeente', 'Stad', 'Town', 'Municipality',)
          
    for place_type, terms in terms.iteritems():
        if any(term in name for term in terms):
            return place_type


def _fill_info_from_google_place(info, google_place):
    # type: (ServiceInfo, dict) -> None
    address = ServiceAddress()

    if google_place['types'] != ['street_address']:
        # This 'place' is just a street, we aren't interested in its place id and name
        address.google_maps_place_id = google_place['place_id']
        address.name = google_place['name']
    loc = google_place['geometry']['location']
    address.coordinates = ndb.GeoPt(loc['lat'], loc['lng'])
    address.value = google_place['formatted_address']
    info.addresses.append(address)

    if google_place.get('website'):
        website_url = validate_url(google_place['website'])
        if website_url:
            logging.debug('_create_service_info google_place.website_url: %s', website_url)
            website = SyncedNameValue()
            website.value = website_url
            info.websites.append(website)
    
    logging.info('google_place.types: %s', google_place['types'])
    for place_type in google_place['types']:
        if place_type not in PlaceType.all():
            continue
        place_type_details = PLACE_DETAILS.get(place_type)
        if place_type_details:
            if place_type_details.replaced_by:
                place_type = place_type_details.replaced_by
            if place_type not in info.place_types:
                info.place_types.append(place_type)
                
    if info.place_types:
        logging.info('service_info.place_types: %s', info.place_types)


def _get_google_place_from_coordinates_and_name(keywords, coordinates, radius, place_type, language):
    google_maps_key = get_server_settings().googleMapsKey
    query = {
        'key': google_maps_key,
        'location': '%s,%s' % tuple(coordinates),
        'radius': radius,
        'keyword': ' '.join(keywords),
        'language': language
    }
    if place_type:
        query['type'] = place_type

    if DEBUG:
        logging.debug('Searching for nearby places %s', query)
    url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?%s' % urlencode(query, doseq=True)

    result = urlfetch.fetch(url)
    if result.status_code != 200:
        raise Exception('Error while fetching places: %s' % result.content)
    response = json.loads(result.content)
    if response['status'] == 'ZERO_RESULTS':
        return None
    elif response['status'] == 'OK':
        if DEBUG:
            logging.debug('Place results: %s', response['results'])
        place = response['results'][0]
        query = {
            'key': google_maps_key,
            'placeid': place['place_id'],
            'language': language,
            'fields': 'formatted_address,geometry,name,place_id,type,url,formatted_phone_number,website,opening_hours'
        }
        details = urlfetch.fetch('https://maps.googleapis.com/maps/api/place/details/json?%s' % urlencode(query))
        if details.status_code == 200:
            return json.loads(details.content)['result']
        else:
            raise Exception('Error while fetching place details: %s' % details.content)

    else:
        raise Exception('Error while fetching places: %s' % response)
