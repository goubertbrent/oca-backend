# -*- coding: utf-8 -*-
# Copyright 2021 Green Valley NV
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
import cloudstorage
import logging
from google.appengine.ext import ndb
from google.appengine.ext.deferred import deferred
from google.appengine.ext.ndb.key import Key
from typing import List, Tuple

from mcfw.exceptions import HttpForbiddenException, HttpBadRequestException
from rogerthat.bizz.communities.communities import get_community
from rogerthat.bizz.communities.models import CommunityGeoFence
from rogerthat.bizz.maps.poi.search import cleanup_poi_index, re_index_poi, search_poi
from rogerthat.bizz.maps.poi.models import PointOfInterest, POIStatus
from rogerthat.bizz.maps.poi.to import PointOfInterestTO, POILocationTO
from rogerthat.bizz.maps.services import SearchTag
from rogerthat.dal.profile import get_service_profile
from rogerthat.models import OpeningHours
from rogerthat.rpc import users
from rogerthat.utils import try_or_defer
from rogerthat.utils.location import haversine
from solutions.common.bizz.opening_hours import populate_opening_hours
from solutions.common.bizz.settings import get_media_item_models_from_to
from solutions.common.models.forms import UploadedFile


class GeoFenceException(HttpBadRequestException):
    pass


def get_point_of_interest(poi_id, service_user):
    # type: (int, users.User) -> PointOfInterest
    service_profile = get_service_profile(service_user)
    poi = PointOfInterest.create_key(poi_id).get()  # type: PointOfInterest
    if service_profile.community_id != poi.community_id:
        raise HttpForbiddenException()
    return poi


def create_point_of_interest(data, service_user):
    # type: (PointOfInterestTO, users.User) -> PointOfInterest
    service_profile = get_service_profile(service_user)
    poi = PointOfInterest(community_id=service_profile.community_id)
    _populate_poi(data, poi)
    poi.put()
    try_or_defer(re_index_poi, poi, get_community(service_profile.community_id))
    return poi


def update_point_of_interest(poi_id, data, service_user):
    # type: (int, PointOfInterestTO, users.User) -> PointOfInterest
    poi = get_point_of_interest(poi_id, service_user)
    _populate_poi(data, poi)
    poi.put()
    try_or_defer(re_index_poi, poi, get_community(poi.community_id))
    return poi


def delete_point_of_interest(poi_id, service_user):
    # type: (int, users.User) -> None
    poi = get_point_of_interest(poi_id, service_user)
    poi_key = poi.key
    poi_key.delete()
    try_or_defer(cleanup_poi_index, poi_id)
    deferred.defer(_cleanup_uploaded_files, poi_key)


def list_point_of_interest(community_id, status=None, search_query=None, cursor=None, page_size=50):
    # type: (int, int, str, str, int) -> Tuple[List[PointOfInterest], str, bool]
    tags = [SearchTag.community(community_id)]
    if status is not None:
        tags.append(SearchTag.poi_status(status))
    new_cursor, result_ids = search_poi(tags, [], cursor=cursor, limit=page_size, search_qry=search_query)
    keys = [PointOfInterest.create_key(long(uid)) for uid in result_ids]
    poi_list = ndb.get_multi(keys)  # type: List[PointOfInterest]
    has_more = len(result_ids) == page_size
    return poi_list, new_cursor, has_more


def get_timezone_for_location(location):
    # type: (POILocationTO) -> str
    # Some shortcuts to save a bit on gmaps costs
    tz_mapping = {
        'BE': 'Europe/Brussels',
        'NL': 'Europe/Amsterdam',
        'DE': 'Europe/Berlin',
        'GB': 'Europe/London',
        'SE': 'Europe/Stockholm',
        'NO': 'Europe/Oslo',
        'ZA': 'Africa/Johannesburg',
    }
    if location.country in tz_mapping:
        return tz_mapping[location.country]
    logging.debug("country: %s", location.country)
    raise Exception("Unable to get timezone, country not in mapping")
# For now only allow countries in the mapping
#     timezone_info = get_timezone_from_latlon(location.coordinates.lat, location.coordinates.lon)
#     return timezone_info['timeZoneId']


def _check_geo_fence(model):
    # type: (PointOfInterest) -> bool
    community_geo_fence = CommunityGeoFence.create_key(model.community_id).get()  # type: CommunityGeoFence
    if not community_geo_fence or not community_geo_fence.geometry:
        logging.error('No CommunityGeoFence geometry set for community %d', model.community_id)
        return False

    distance = long(haversine(model.location.coordinates.lon,
                              model.location.coordinates.lat,
                              community_geo_fence.geometry.center.lon,
                              community_geo_fence.geometry.center.lat) * 1000)

    logging.debug('Distance: %d, max allowed: %d', distance, community_geo_fence.geometry.max_distance)
    return distance <= community_geo_fence.geometry.max_distance


def _populate_poi(data, model):
    # type: (PointOfInterestTO, PointOfInterest) -> PointOfInterest
    model.title = data.title
    model.description = data.description
    model.location = data.location.to_model(get_timezone_for_location(data.location))
    if not _check_geo_fence(model):
        raise GeoFenceException('The location of the point of interest is too far from your city.')
    model.main_place_type = data.main_place_type
    model.place_types = data.place_types
    model.opening_hours = populate_opening_hours(data.opening_hours, OpeningHours())
    if model.has_complete_key():
        media_to_get = [Key(urlsafe=media.file_reference) for media in data.media if media.file_reference]
        model.media = get_media_item_models_from_to(data.media, ndb.get_multi(media_to_get))
    model.visible = data.visible
    if model.visible:
        model.status = POIStatus.VISIBLE if model.has_complete_info else POIStatus.INCOMPLETE
    else:
        model.status = POIStatus.INVISIBLE
    return model


def _cleanup_uploaded_files(poi_key):
    for uploaded_file in UploadedFile.list_by_poi(poi_key):  # type: UploadedFile
        for scaled_image in uploaded_file.scaled_images:
            _delete_from_cloudstorage(scaled_image.cloudstorage_path)
        _delete_from_cloudstorage(uploaded_file.cloudstorage_path)
        uploaded_file.key.delete()


def _delete_from_cloudstorage(path):
    try:
        cloudstorage.delete(path)
    except cloudstorage.NotFoundError:
        pass

