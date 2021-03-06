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

from babel import Locale
from google.appengine.ext import db, ndb
from google.appengine.ext.deferred import deferred
from typing import List, Iterable

from mcfw.cache import cached
from mcfw.properties import azzert
from mcfw.rpc import returns, arguments
from rogerthat.bizz.communities.models import Community, CommunityAutoConnectedService, CommunityGeoFence, \
    CommunityUserStatsHistory, CommunityUserStats
from rogerthat.bizz.communities.to import BaseCommunityTO
from rogerthat.bizz.friend_helper import FriendHelper
from rogerthat.bizz.job import hookup_with_default_services, run_job
from rogerthat.dal.profile import get_user_profiles_by_community
from rogerthat.models import ServiceIdentity, App, NdbUserProfile, \
    NdbServiceProfile
from rogerthat.models.news import NewsGroup
from rogerthat.rpc import users
from rogerthat.to.friends import FRIEND_TYPE_SERVICE
from rogerthat.utils.service import add_slash_default


# Non-transactional to ensure the cache is used, even when fetched during a transaction.
@ndb.non_transactional()
@db.non_transactional()
def get_community(community_id):
    # type: (int) -> Community
    # todo communities remove after testing
    azzert(community_id, 'get_community failed to provide a community_id')
    return Community.create_key(community_id).get()


def get_communities_by_id(community_ids):
    # type: (List[int]) -> List[Community]
    return ndb.get_multi([Community.create_key(community_id) for community_id in community_ids])


def create_community(data):
    # type: (BaseCommunityTO) -> Community
    from rogerthat.bizz.news.groups import setup_news_stream_community
    community = _populate_community(Community(), data)
    community.put()
    deferred.defer(setup_news_stream_community, community.id)
    return community


def delete_community(community_id, delete=False):
    from shop.models import Customer
    from rogerthat.bizz.communities.homescreen import CommunityHomeScreen
    from rogerthat.bizz.maps.poi import PointOfInterest
    from rogerthat.models.news import NewsStream
    from rogerthat.bizz.communities.homescreen import delete_home_screen, TEST_HOME_SCREEN_ID
    logging.debug('Checking if community can be deleted: %s', community_id)
    community = get_community(community_id)
    if not community:
        logging.debug('Community not found')
        raise Exception('Community not found')

    can_delete = True
    app_ids = [a.app_id for a in App.list_by_community_id(community_id)]
    if app_ids:
        logging.debug('community used in apps:%s', app_ids)
        can_delete = False

    user_profile_count = NdbUserProfile.list_by_community(community_id).count(None)
    if user_profile_count > 0:
        logging.debug('community used in users:%s', user_profile_count)
        can_delete = False

    service_profile_count = NdbServiceProfile.list_by_community(community_id).count(None)
    if service_profile_count > 0:
        logging.debug('community used in services:%s', service_profile_count)
        can_delete = False

    customer_count = Customer.list_by_community_id(community_id).count(None)
    if customer_count > 0:
        logging.debug('community used in customers:%s', customer_count)
        can_delete = False

    if PointOfInterest.list_by_community(community_id).count(1):
        logging.debug('community used for one or more PointOfInterest')
        can_delete = False

    if not can_delete:
        raise Exception('This community is still in use and cannot be deleted')

    logging.debug('Its okay to delete')
    if delete:
        keys = [
            community.key,
            CommunityGeoFence.create_key(community_id),
            CommunityUserStatsHistory.create_key(community_id),
            CommunityUserStats.create_key(community_id),
            NewsStream.create_key(community_id),
        ]
        keys.extend(NewsGroup.list_by_community_id(community_id).fetch(keys_only=True))
        delete_home_screen(community_id, TEST_HOME_SCREEN_ID)
        for key in CommunityHomeScreen.list_by_community(community_id).fetch(keys_only=True):
            delete_home_screen(community_id, key.id())
            keys.append(keys)
        ndb.delete_multi(keys)


def update_community(community_id, data):
    # type: (int, BaseCommunityTO) -> Community
    from rogerthat.bizz.service import ServiceIdentityDoesNotExistException
    auto_connected_identities = db.get([
        ServiceIdentity.keyFromUser(add_slash_default(users.User(acs.service_email)))
        for acs in data.auto_connected_services
    ])
    for acs, si in zip(data.auto_connected_services, auto_connected_identities):
        if not si:
            raise ServiceIdentityDoesNotExistException(acs.service_email)
    community = get_community(community_id)
    old_embedded_apps = community.embedded_apps
    old_acs = community.auto_connected_service_emails
    _populate_community(community, data)
    new_acs = [s for s in community.auto_connected_services if s.service_email not in old_acs]
    if new_acs:
        logging.info('There are new auto-connected services for community %s(%s): %s', community.name, community.id,
                     new_acs)
        deferred.defer(connect_auto_connected_service, community_id, new_acs)
    if set(old_embedded_apps).symmetric_difference(community.embedded_apps):
        from rogerthat.bizz.embedded_applications import send_update_all_embedded_apps
        deferred.defer(send_update_all_embedded_apps, community.id, _countdown=2)
    community.put()
    return community


def _populate_community(community, data):
    # type: (Community, BaseCommunityTO) -> Community
    community.auto_connected_services = [CommunityAutoConnectedService(service_email=acs.service_email,
                                                                       removable=acs.removable)
                                         for acs in data.auto_connected_services]
    community.country = data.country
    community.default_app = data.default_app
    community.demo = data.demo
    community.embedded_apps = data.embedded_apps
    community.features = data.features
    community.customization_features = data.customization_features
    community.main_service = data.main_service
    community.name = data.name
    community.signup_enabled = data.signup_enabled
    return community


def get_communities_by_country(country_code, live_only=True):
    # type: (str, bool) -> Iterable[Community]
    if not country_code:
        country_code = None
    qry = Community.list_by_country(country_code)  # type: Iterable[Community]
    if live_only:
        result = (c for c in qry if c.signup_enabled)
    else:
        result = qry
    return sorted(result, key=lambda c: c.name)


# Cached for 30 minutes
@cached(0, 1800)
@returns([unicode])
@arguments()
def get_community_countries():
    return list({c.country for c in Community.list_signup_enabled()})


def get_all_community_countries():
    locale = Locale('en', 'GB')
    return [{'code': c.country, 'name': locale.territories[c.country]}
            for c in Community.list_countries() if c.country]


def connect_auto_connected_service(community_id, new_acs):
    # type: (int, List[CommunityAutoConnectedService]) -> None
    for acs in new_acs:
        helper = FriendHelper.serialize(users.User(acs.service_identity_email), FRIEND_TYPE_SERVICE)
        run_job(get_user_profiles_by_community, [community_id],
                hookup_with_default_services.run_for_auto_connected_service, [[acs], helper])
