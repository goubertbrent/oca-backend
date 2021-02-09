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
import functools

from mcfw.consts import REST_TYPE_TO
from mcfw.exceptions import HttpForbiddenException
from mcfw.restapi import rest
from mcfw.rpc import arguments, returns
from poi import create_point_of_interest, update_point_of_interest, delete_point_of_interest, get_point_of_interest, \
    list_point_of_interest
from rogerthat.dal.profile import get_service_profile
from rogerthat.rpc import users
from solutions import translate
from solutions.common.bizz import SolutionModule
from solutions.common.dal import get_solution_settings
from to import PointOfInterestTO, PointOfInterestListTO


def require_module(required_module):
    def wrap(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            settings = get_solution_settings(users.get_current_user())
            if required_module not in settings.modules:
                msg = translate(settings.main_language, 'no_permission')
                raise HttpForbiddenException(msg)
            return f(*args, **kwargs)
        return wrapped
    return wrap


@rest('/common/point-of-interest', 'get', silent=True, silent_result=True)
@returns(PointOfInterestListTO)
@arguments(query=unicode, status=(int, long), cursor=unicode, page_size=(int, long))
def rest_list_poi(query=None, status=None, cursor=None, page_size=50):
    service_profile = get_service_profile(users.get_current_user())
    results, new_cursor, has_more = list_point_of_interest(service_profile.community_id, status, query, cursor,
                                                           page_size)
    return PointOfInterestListTO(new_cursor, has_more, [PointOfInterestTO.from_model(m) for m in results])


@require_module(SolutionModule.POINTS_OF_INTEREST)
@rest('/common/point-of-interest', 'post', type=REST_TYPE_TO, silent=True, silent_result=True)
@returns(PointOfInterestTO)
@arguments(data=PointOfInterestTO)
def rest_create_poi(data):
    return PointOfInterestTO.from_model(create_point_of_interest(data, users.get_current_user()))


@rest('/common/point-of-interest/<poi_id:[^/]+>', 'get', silent=True, silent_result=True)
@returns(PointOfInterestTO)
@arguments(poi_id=(int, long))
def rest_get_poi(poi_id):
    return PointOfInterestTO.from_model(get_point_of_interest(poi_id, users.get_current_user()))


@require_module(SolutionModule.POINTS_OF_INTEREST)
@rest('/common/point-of-interest/<poi_id:[^/]+>', 'put', silent=True, silent_result=True, type=REST_TYPE_TO)
@returns(PointOfInterestTO)
@arguments(poi_id=(int, long), data=PointOfInterestTO)
def rest_update_poi(poi_id, data):
    return PointOfInterestTO.from_model(update_point_of_interest(poi_id, data, users.get_current_user()))


@require_module(SolutionModule.POINTS_OF_INTEREST)
@rest('/common/point-of-interest/<poi_id:[^/]+>', 'delete', silent=True, silent_result=True)
@returns()
@arguments(poi_id=(int, long))
def rest_delete_poi(poi_id):
    delete_point_of_interest(poi_id, users.get_current_user())
