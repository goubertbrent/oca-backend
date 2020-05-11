# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
# NOTICE: THIS FILE HAS BEEN MODIFIED BY GREEN VALLEY BELGIUM NV IN ACCORDANCE WITH THE APACHE LICENSE VERSION 2.0
# Copyright 2018 GIG Technology NV
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
# @@license_version:1.6@@

import base64
import os
from datetime import datetime

from google.appengine.ext import ndb

import mc_unittest
from mcfw.rpc import serialize_complex_value
from rogerthat.bizz.friends import makeFriends
from rogerthat.bizz.news import create_push_notification, match_roles_of_item, \
    get_groups_for_user
from rogerthat.bizz.news.matching import should_match_location, \
    setup_default_settings, _create_news_item_match
from rogerthat.bizz.profile import create_service_profile, create_service_identity_user, \
    create_user_profile
from rogerthat.bizz.system import get_profile_addresses, \
    delete_profile_addresses, add_profile_address, update_profile_address
from rogerthat.consts import DAY
from rogerthat.exceptions.news import CannotUnstickNewsException
from rogerthat.models import App, ServiceIdentity, ServiceRole, \
    UserProfileInfoAddress, UserProfileInfo, UserProfile, UserAddressType
from rogerthat.models.news import NewsItem, NewsGroup, NewsSettingsService, \
    NewsSettingsServiceGroup, NewsItemAddress, NewsSettingsUser, NewsStream
from rogerthat.models.properties.news import NewsItemStatistics
from rogerthat.rpc import users
from rogerthat.service.api import news, system
from rogerthat.to import GeoPointTO
from rogerthat.to.messaging import MemberTO
from rogerthat.to.news import NewsActionButtonTO, NewsItemTO, NewsSenderTO, \
    NewsFeedNameTO, BaseMediaTO, NewsLocationsTO, NewsGeoAddressTO, \
    NewsAddressTO, NewsTargetAudienceTO
from rogerthat.to.system import AddProfileAddressRequestTO, UpdateProfileAddressRequestTO
from rogerthat.utils import now
from rogerthat.utils.app import create_app_user_by_email
from rogerthat.utils.location import haversine
from rogerthat_tests import set_current_user


# TODO: this file is a mess, cleanup


class NewsTest(mc_unittest.TestCase):
    user = users.User(u'test@example.com')
    app_id = 'be-loc'

    def setUp(self, datastore_hr_probability=1):
        super(NewsTest, self).setUp(datastore_hr_probability)
        self._create_news_groups(self.app_id)
        create_service_profile(self.user, u'test name', supported_app_ids=[self.app_id])

    @classmethod
    def _create_news_item(cls, num, sticky=False, news_type=NewsItem.TYPE_NORMAL, role_ids=None, tags=None,
                          feed_names=None, use_media=False, app_ids=None, locations=None,
                          group_type=NewsGroup.TYPE_CITY,
                          use_image_url=False, use_image_url_http=False):
        def _get_file_contents(path):
            f = open(path, "rb")
            try:
                return f.read()
            finally:
                f.close()

        current_dir = os.path.dirname(__file__)
        image_path = os.path.join(current_dir, 'news_image.jpg')
        image = _get_file_contents(image_path)
        base_64_image = 'data:image/png,%s' % base64.b64encode(image)

        if use_image_url:
            if use_image_url_http:
                url = u'http://dashboard.onzestadapp.be/static/images/public/logo.png'
            else:
                url = u'https://dashboard.onzestadapp.be/static/images/public/logo.png'
            media = BaseMediaTO(type='image', content=url)
        elif use_media:
            media = BaseMediaTO(type='image', content=base_64_image)
        else:
            media = None

        title = u'test news title %d' % num
        message = u'test news message %d' % num
        action_button = NewsActionButtonTO(id_=u'test_%d' % num,
                                           action=u'smi://nonexisting_%d' % num,
                                           caption=u'This button does nothing %d' % num)

        target_audience = NewsTargetAudienceTO()
        target_audience.min_age = 0
        target_audience.max_age = 200
        target_audience.gender = UserProfile.GENDER_MALE_OR_FEMALE
        target_audience.connected_users_only = True

        return news.publish(sticky=sticky,
                            sticky_until=now() + DAY if sticky else 0,
                            title=title,
                            message=message,
                            image=None if media else base_64_image,
                            news_type=news_type,
                            action_buttons=[action_button],
                            qr_code_content=None,
                            qr_code_caption=None,
                            news_id=None,
                            service_identity=None,
                            target_audience=target_audience,
                            app_ids=app_ids if app_ids else [App.APP_ID_ROGERTHAT],
                            scheduled_at=0,
                            flags=NewsItem.DEFAULT_FLAGS,
                            role_ids=role_ids,
                            tags=tags,
                            feed_names=feed_names,
                            media=media,
                            locations=locations,
                            group_type=group_type)

    @classmethod
    def _update_news_item(cls, news_id, num, app_ids, group_type=None):
        sticky = False
        news_type = NewsItem.TYPE_NORMAL
        title = u'test news title %d' % num
        message = u'test news message %d' % num
        action_button = NewsActionButtonTO(id_=u'test_%d' % num,
                                           action=u'smi://nonexisting_%d' % num,
                                           caption=u'This button does nothing %d' % num)
        return news.publish(sticky=sticky, sticky_until=now() + DAY if sticky else 0, scheduled_at=0,
                            title=title, message=message,
                            news_type=news_type,
                            action_buttons=[action_button],
                            qr_code_content=None, qr_code_caption=None,
                            news_id=news_id,
                            image=None, media=None,
                            app_ids=app_ids,
                            flags=NewsItem.DEFAULT_FLAGS,
                            group_type=group_type)

    def test_publish_news(self):
        with set_current_user(self.user, skip_create_session=True):
            sticky_until = now() + DAY
            news_item = self._create_news_item(1)
            updated_title = u'new and updated title'
            updated_news_item = news.publish(sticky=True, sticky_until=sticky_until, title=updated_title, image=None,
                                             news_id=news_item.id, accept_missing=True)
            self.assertEqual(updated_news_item.sticky, True)
            self.assertEqual(updated_news_item.sticky_until, sticky_until)
            self.assertEqual(updated_news_item.title, updated_title)
            self.assertEqual(updated_news_item.image_url, None)
            self.assertRaises(CannotUnstickNewsException, news.publish, sticky=False, news_id=news_item.id,
                              accept_missing=True)

            result = news.list_news()
            self.assertEqual(1, len(result.result))
            result2 = news.list_news(result.cursor)
            self.assertEqual(0, len(result2.result))

    def test_apn(self):
        news_item = NewsItemTO()
        news_item.id = 41027
        news_item.sender = NewsSenderTO()
        news_item.sender.name = u'Service 1'
        news_item.title = u'Sample news item title'
        news_item.message = u'This is a sample news message. The news item above this one is a preview of the news ' \
                            'item that you are currently creating or editing and gives you a good estimation of how ' \
                            'your post will look like.'
        print create_push_notification(news_item)

        news_item.message = None
        print create_push_notification(news_item)

    def test_properties(self):
        with set_current_user(self.user, skip_create_session=True):
            news_item_id = self._create_news_item(1).id

        news_item = NewsItem.get_by_id(news_item_id)
        app_id = news_item.app_ids[0]
        statistic_property = "reached_age"
        default_stats = getattr(NewsItemStatistics, 'default_age_stats')()

        original_statistics = getattr(news_item.statistics[app_id], statistic_property, default_stats)
        setattr(news_item.statistics[app_id], statistic_property, original_statistics)

    def test_roles_matching(self):
        role_names = ['employee', 'manager', 'g.manager']
        with set_current_user(self.user, skip_create_session=True):
            role_ids = [system.put_role(name, ServiceRole.TYPE_MANAGED) for name in role_names]
            si_user = create_service_identity_user(self.user, ServiceIdentity.DEFAULT)

            app_user_with_roles = create_app_user_by_email(u'app@test.user')
            app_user_without_roles = create_app_user_by_email(u'app@test.user.noroles')
            app_user_half_roles = create_app_user_by_email(u'app@test.half.roles')
            create_user_profile(app_user_with_roles, u'ROLES')
            create_user_profile(app_user_without_roles, u'NO ROLES')
            create_user_profile(app_user_half_roles, u'1/2 ROLES')

            # now the service user has some roles, assign it to the user
            for role_id in role_ids:
                system.add_role_member(role_id, MemberTO.from_user(app_user_with_roles))
            system.add_role_member(role_ids[1], MemberTO.from_user(app_user_half_roles))

            news_item_with_roles = self._create_news_item(111, role_ids=role_ids)
            news_item_without_roles = self._create_news_item(111)

            self.assertTrue(match_roles_of_item(si_user, app_user_with_roles, news_item_without_roles))
            self.assertTrue(match_roles_of_item(si_user, app_user_without_roles, news_item_without_roles))
            self.assertTrue(match_roles_of_item(si_user, app_user_half_roles, news_item_without_roles))

            self.assertTrue(match_roles_of_item(si_user, app_user_with_roles, news_item_with_roles))
            self.assertTrue(match_roles_of_item(si_user, app_user_half_roles, news_item_with_roles))
            self.assertFalse(match_roles_of_item(si_user, app_user_without_roles, news_item_with_roles))

    def test_tag(self):
        tags = [u'bla_bla']
        with set_current_user(self.user, skip_create_session=True):
            news_item = self._create_news_item(123, tags=tags)
            self.assertEqual(tags, news_item.tags)

    def test_feed_names(self):
        feed_names = [NewsFeedNameTO(u'rogerthat', u'bla_ moehaha')]

        with set_current_user(self.user, skip_create_session=True):
            news_item = self._create_news_item(1234, feed_names=feed_names)
            self.assertEqual(serialize_complex_value(feed_names, NewsFeedNameTO, True),
                             serialize_complex_value(news_item.feed_names, NewsFeedNameTO, True))
            self.assertEqual([u'news'], news_item.tags)

    def test_deprecated_image(self):
        with set_current_user(self.user, skip_create_session=True):
            news_item = self._create_news_item(12345, use_media=False, group_type=NewsGroup.TYPE_CITY)
            self.assertTrue(news_item.image_url != None)
            self.assertTrue(news_item.media != None)

    def test_media_image(self):
        with set_current_user(self.user, skip_create_session=True):
            news_item = self._create_news_item(123456, use_media=True, group_type=NewsGroup.TYPE_CITY)
            self.assertTrue(news_item.image_url != None)
            self.assertTrue(news_item.media != None)

    def test_media_image_url(self):
        with set_current_user(self.user, skip_create_session=True):
            news_item = self._create_news_item(2123456, use_media=True, use_image_url=True,
                                               group_type=NewsGroup.TYPE_CITY)
            self.assertTrue(news_item.image_url != None)
            self.assertTrue(news_item.media != None)

    def test_media_image_url_http(self):
        with set_current_user(self.user, skip_create_session=True):
            news_item = self._create_news_item(2123456, use_media=True, use_image_url=True, use_image_url_http=True,
                                               group_type=NewsGroup.TYPE_CITY)
            self.assertTrue(news_item.image_url != None)
            self.assertTrue(news_item.media != None)

    def _create_news_groups(self, app_id, duplicate_in_city_news=False):
        ns = NewsStream(key=NewsStream.create_key(app_id))
        ns.stream_type = None
        ns.should_create_groups = False
        ns.services_need_setup = False
        ns.layout = []
        ns.custom_layout_id = None
        ns.put()

        ng1 = NewsGroup(key=NewsGroup.create_key('be-testing-city'))
        ng1.name = u'%s CITY' % app_id
        ng1.app_id = app_id
        ng1.group_type = NewsGroup.TYPE_CITY
        ng1.filters = []
        ng1.regional = False
        ng1.default_order = 10
        ng1.default_notifications_enabled = True
        ng1.tile = None
        ng1.put()

        ng2 = NewsGroup(key=NewsGroup.create_key('be-testing-events'))
        ng2.name = u'%s EVENTS' % app_id
        ng2.app_id = app_id
        ng2.group_type = NewsGroup.TYPE_EVENTS
        ng2.filters = []
        ng2.regional = False
        ng2.default_order = 30
        ng2.default_notifications_enabled = False
        ng2.tile = None
        ng2.put()

        ng4 = NewsGroup(key=NewsGroup.create_key('be-testing-promo'))
        ng4.name = u'%s PROMOTIONS' % app_id
        ng4.app_id = app_id
        ng4.group_type = NewsGroup.TYPE_PROMOTIONS
        ng4.filters = NewsGroup.PROMOTIONS_FILTERS
        ng4.regional = False
        ng4.default_order = 70
        ng4.default_notifications_enabled = True
        ng4.tile = None
        ng4.put()

        ng5 = NewsGroup(key=NewsGroup.create_key('be-testing-promo-regional'))
        ng5.name = u'%s PROMOTIONS (regional)' % app_id
        ng5.app_id = app_id
        ng5.group_type = NewsGroup.TYPE_PROMOTIONS
        ng5.filters = NewsGroup.PROMOTIONS_FILTERS
        ng5.regional = True
        ng5.default_order = 70
        ng5.default_notifications_enabled = True
        ng5.tile = None
        ng5.put()

        ng6 = NewsGroup(key=NewsGroup.create_key('be-testing-traffic'))
        ng6.name = u'%s TRAFFIC' % app_id
        ng6.app_id = app_id
        ng6.group_type = NewsGroup.TYPE_TRAFFIC
        ng6.filters = []
        ng6.regional = False
        ng6.default_order = 50
        ng6.default_notifications_enabled = False
        ng6.tile = None
        ng6.put()

        nss = NewsSettingsService(key=NewsSettingsService.create_key(self.user))
        nss.default_app_id = app_id
        nss.setup_needed_id = 0
        nss.groups = [
            NewsSettingsServiceGroup(group_type=NewsGroup.TYPE_CITY, filter=None),
            NewsSettingsServiceGroup(group_type=NewsGroup.TYPE_EVENTS, filter=None)
        ]
        nss.duplicate_in_city_news = duplicate_in_city_news
        nss.put()

    def test_news_stream(self):
        with set_current_user(self.user, skip_create_session=True):
            news_item_1_to = self._create_news_item(1234567, use_media=True, app_ids=[self.app_id],
                                                    group_type=NewsGroup.TYPE_CITY)
            news_item_1 = NewsItem.create_key(news_item_1_to.id).get()
            self.assertEqual(news_item_1.group_types_ordered, [NewsGroup.TYPE_CITY])
            self.assertEqual(news_item_1.group_types, [NewsGroup.TYPE_CITY])
            self.assertEqual(news_item_1.group_ids, [u'be-testing-city'])
            self.assertEqual(news_item_1.group_types, [news_item_1_to.group_type])

            news_item_1_to = self._update_news_item(news_item_1_to.id, 12345678, news_item_1.app_ids,
                                                    group_type=NewsGroup.TYPE_EVENTS)
            news_item_1 = NewsItem.create_key(news_item_1_to.id).get()
            self.assertEqual(news_item_1.group_types_ordered, [NewsGroup.TYPE_EVENTS])
            self.assertEqual(news_item_1.group_types, [NewsGroup.TYPE_EVENTS])
            self.assertEqual(news_item_1.group_ids, [u'be-testing-events'])
            self.assertEqual(news_item_1.group_types, [news_item_1_to.group_type])

            news_item_2_to = self._create_news_item(12345678, use_media=True, app_ids=[self.app_id],
                                                    group_type=NewsGroup.TYPE_EVENTS)
            news_item_2 = NewsItem.create_key(news_item_2_to.id).get()
            self.assertEqual(news_item_2.group_types_ordered, [NewsGroup.TYPE_EVENTS])
            self.assertEqual(news_item_2.group_types, [NewsGroup.TYPE_EVENTS])
            self.assertEqual(news_item_2.group_ids, [u'be-testing-events'])
            self.assertEqual(news_item_2.group_types, [news_item_2_to.group_type])

            news_item_2_to = self._update_news_item(news_item_2_to.id, 1234567, news_item_2.app_ids,
                                                    group_type=NewsGroup.TYPE_CITY)
            news_item_2 = NewsItem.create_key(news_item_2_to.id).get()
            self.assertEqual(news_item_2.group_types_ordered, [NewsGroup.TYPE_CITY])
            self.assertEqual(news_item_2.group_types, [NewsGroup.TYPE_CITY])
            self.assertEqual(news_item_2.group_ids, [u'be-testing-city'])
            self.assertEqual(news_item_2.group_types, [news_item_2_to.group_type])

    def test_news_stream_duplicate_in_city_news(self):
        self._create_news_groups(self.app_id, True)

        with set_current_user(self.user, skip_create_session=True):
            news_item_1_to = self._create_news_item(1234567, use_media=True, app_ids=[self.app_id])
            news_item_1 = NewsItem.create_key(news_item_1_to.id).get()
            self.assertEqual(news_item_1.group_types_ordered, [NewsGroup.TYPE_CITY])
            self.assertEqual(news_item_1.group_types, [NewsGroup.TYPE_CITY])
            self.assertEqual(news_item_1.group_ids, [u'be-testing-city'])
            self.assertEqual(news_item_1.group_types, [news_item_1_to.group_type])

            news_item_1_to = self._update_news_item(news_item_1_to.id, 12345678, news_item_1.app_ids,
                                                    group_type=NewsGroup.TYPE_EVENTS)
            news_item_1 = NewsItem.create_key(news_item_1_to.id).get()
            self.assertEqual(news_item_1.group_types_ordered, [NewsGroup.TYPE_EVENTS, NewsGroup.TYPE_CITY])
            self.assertEqual(news_item_1.group_types, [NewsGroup.TYPE_EVENTS, NewsGroup.TYPE_CITY])
            self.assertEqual(news_item_1.group_ids, [u'be-testing-events', u'be-testing-city'])
            self.assertEqual(news_item_1.group_types, [news_item_1_to.group_type, NewsGroup.TYPE_CITY])

            news_item_2_to = self._create_news_item(12345678, use_media=True, app_ids=[self.app_id],
                                                    group_type=NewsGroup.TYPE_EVENTS)
            news_item_2 = NewsItem.create_key(news_item_2_to.id).get()
            self.assertEqual(news_item_2.group_types_ordered, [NewsGroup.TYPE_EVENTS, NewsGroup.TYPE_CITY])
            self.assertEqual(news_item_2.group_types, [NewsGroup.TYPE_EVENTS, NewsGroup.TYPE_CITY])
            self.assertEqual(news_item_2.group_ids, [u'be-testing-events', u'be-testing-city'])
            self.assertEqual(news_item_2.group_types, [news_item_2_to.group_type, NewsGroup.TYPE_CITY])

            news_item_2_to = self._update_news_item(news_item_2_to.id, 1234567, news_item_2.app_ids,
                                                    group_type=NewsGroup.TYPE_CITY)
            news_item_2 = NewsItem.create_key(news_item_2_to.id).get()
            self.assertEqual(news_item_2.group_types_ordered, [NewsGroup.TYPE_CITY])
            self.assertEqual(news_item_2.group_types, [NewsGroup.TYPE_CITY])
            self.assertEqual(news_item_2.group_ids, [u'be-testing-city'])
            self.assertEqual(news_item_2.group_types, [news_item_2_to.group_type])

    def test_news_stream_group_types(self):
        with set_current_user(self.user, skip_create_session=True):
            news_item_1_to = self._create_news_item(1234567, use_media=True, app_ids=[self.app_id],
                                                    group_type=NewsGroup.TYPE_CITY)
            news_item_1 = NewsItem.create_key(news_item_1_to.id).get()
            self.assertEqual(news_item_1.group_types, [NewsGroup.TYPE_CITY])
            self.assertEqual(news_item_1.group_ids, [u'be-testing-city'])
            self.assertEqual(news_item_1.group_types, [news_item_1_to.group_type])

            news_item_1_to = self._update_news_item(news_item_1_to.id, 12345678, news_item_1.app_ids,
                                                    group_type=NewsGroup.TYPE_EVENTS)
            news_item_1 = NewsItem.create_key(news_item_1_to.id).get()
            self.assertEqual(news_item_1.group_types, [NewsGroup.TYPE_EVENTS])
            self.assertEqual(news_item_1.group_ids, [u'be-testing-events'])
            self.assertEqual(news_item_1.group_types, [news_item_1_to.group_type])

            news_item_2_to = self._create_news_item(12345678, use_media=True, app_ids=[self.app_id],
                                                    group_type=NewsGroup.TYPE_EVENTS)
            news_item_2 = NewsItem.create_key(news_item_2_to.id).get()
            self.assertEqual(news_item_2.group_types, [NewsGroup.TYPE_EVENTS])
            self.assertEqual(news_item_2.group_ids, [u'be-testing-events'])
            self.assertEqual(news_item_2.group_types, [news_item_2_to.group_type])

            news_item_2_to = self._update_news_item(news_item_2_to.id, 1234567, news_item_2.app_ids,
                                                    group_type=NewsGroup.TYPE_CITY)
            news_item_2 = NewsItem.create_key(news_item_2_to.id).get()
            self.assertEqual(news_item_2.group_types, [NewsGroup.TYPE_CITY])
            self.assertEqual(news_item_2.group_ids, [u'be-testing-city'])
            self.assertEqual(news_item_2.group_types, [news_item_2_to.group_type])

    def _create_addresses(self):
        addresses = [
            {
                u'city': u'ACity',
                u'house_nr': u'1',
                u'street_name': u'AStreet',
                u'country_code': u'BE',
                u'house_bus': u'',
                u'zip_code': u'AZipCode',
                u'geo': {
                    u'lat': 51.092597,
                    u'lng': 3.8194548,
                    u'distance': 100
                }
            },
            {
                u'city': u'ACity',
                u'house_nr': u'3',
                u'street_name': u'AStreet',
                u'country_code': u'BE',
                u'house_bus': u'',
                u'zip_code': u'AZipCode',
                u'geo': {
                    u'lat': 51.092597,
                    u'lng': 3.8194548,
                    u'distance': 500
                }
            },
            {
                u'city': u'ACity',
                u'house_nr': u'1',
                u'street_name': u'BStreet',
                u'country_code': u'BE',
                u'house_bus': u'',
                u'zip_code': u'AZipCode',
                u'geo': {
                    u'lat': 51.0954861,
                    u'lng': 3.8293991,
                    u'distance': 100
                }
            },
            {
                u'city': u'ACity',
                u'house_nr': u'3',
                u'street_name': u'BStreet',
                u'country_code': u'BE',
                u'house_bus': u'',
                u'zip_code': u'AZipCode',
                u'geo': {
                    u'lat': 51.0954861,
                    u'lng': 3.8293991,
                    u'distance': 800
                }
            },
            {
                u'city': u'BCity',
                u'house_nr': u'1',
                u'street_name': u'AStreet',
                u'country_code': u'BE',
                u'house_bus': u'',
                u'zip_code': u'BZipCode',
                u'geo': {
                    u'lat': 51.0823564,
                    u'lng': 3.5744037,
                    u'distance': 100
                }
            }
        ]

        dt = datetime.now()
        address_hashes = {}
        street_hashes = {}
        for i, a in enumerate(addresses):
            a['address_uid'] = UserProfileInfoAddress.create_uid(
                [a['country_code'], a['zip_code'], a['street_name'], a['house_nr'], a['house_bus']])
            a['street_uid'] = UserProfileInfoAddress.create_uid([a['country_code'], a['zip_code'], a['street_name']])

            upia = UserProfileInfoAddress(created=dt,
                                          address_uid=a['address_uid'],
                                          street_uid=a['street_uid'],
                                          label=u'Work',
                                          geo_location=ndb.GeoPt(a['geo']['lat'],
                                                                 a['geo']['lng']),
                                          distance=a['geo']['distance'],
                                          street_name=a['street_name'],
                                          house_nr=a['house_nr'],
                                          bus_nr=a['house_bus'],
                                          zip_code=a['zip_code'],
                                          city=a['city'],
                                          country_code=a['country_code'])

            app_user = users.User('user_%s@example.com:%s' % (i, self.app_id))
            up = create_user_profile(app_user, app_user.email(), language=u'nl')
            up.birthdate = 0
            up.birth_day = UserProfile.get_birth_day_int(up.birthdate)
            up.gender = UserProfile.GENDER_MALE
            up.put()

            upi = UserProfileInfo(key=UserProfileInfo.create_key(app_user))
            upi.addresses = [upia]
            upi.put()

            makeFriends(create_service_identity_user(self.user), app_user, None, None, None, False, False)

            profile_addresses = get_profile_addresses(app_user)
            self.assertEqual(len(profile_addresses), 1)
            delete_profile_addresses(app_user, [a['address_uid']])
            profile_addresses = get_profile_addresses(app_user)
            self.assertEqual(len(profile_addresses), 0)

            add_request = AddProfileAddressRequestTO()
            add_request.type = UserAddressType.WORK
            add_request.label = u"Work"
            add_request.geo_location = GeoPointTO()
            add_request.geo_location.lat = a['geo']['lat']
            add_request.geo_location.lon = a['geo']['lng']
            add_request.distance = a['geo']['distance']
            add_request.street_name = a['street_name']
            add_request.house_nr = a['house_nr']
            add_request.bus_nr = a['house_bus']
            add_request.zip_code = a['zip_code']
            add_request.city = a['city']
            add_request.country_code = a['country_code']

            address_uid = add_profile_address(app_user, add_request).address_uid
            self.assertEqual(address_uid, a['address_uid'])
            upi = UserProfileInfo.create_key(app_user).get()
            tmp_upia = upi.get_address(address_uid)
            self.assertEqual(tmp_upia.label, add_request.label)
            self.assertEqual(tmp_upia.distance, add_request.distance)
            profile_addresses = get_profile_addresses(app_user)
            self.assertEqual(len(profile_addresses), 1)

            update_request_1 = UpdateProfileAddressRequestTO()
            update_request_1.uid = unicode(address_uid)
            update_request_1.type = UserAddressType.WORK
            update_request_1.label = u'Work Updated'
            update_request_1.geo_location = GeoPointTO()
            update_request_1.geo_location.lat = a['geo']['lat']
            update_request_1.geo_location.lon = a['geo']['lng']
            update_request_1.distance = 30000000
            update_request_1.street_name = a['street_name']
            update_request_1.house_nr = a['house_nr']
            update_request_1.bus_nr = a['house_bus']
            update_request_1.zip_code = a['zip_code']
            update_request_1.city = a['city']
            update_request_1.country_code = a['country_code']

            address_uid = update_profile_address(app_user, update_request_1).address_uid
            self.assertEqual(address_uid, a['address_uid'])
            upi = UserProfileInfo.create_key(app_user).get()
            tmp_upia = upi.get_address(address_uid)
            self.assertEqual(tmp_upia.label, update_request_1.label)
            self.assertEqual(tmp_upia.distance, update_request_1.distance)
            profile_addresses = get_profile_addresses(app_user)
            self.assertEqual(len(profile_addresses), 1)

            update_request_2 = UpdateProfileAddressRequestTO()
            update_request_2.uid = unicode(address_uid)
            update_request_2.type = UserAddressType.WORK
            update_request_2.label = u'Work replace'
            update_request_2.geo_location = GeoPointTO()
            update_request_2.geo_location.lat = a['geo']['lat']
            update_request_2.geo_location.lon = a['geo']['lng']
            update_request_2.distance = a['geo']['distance']
            update_request_2.street_name = a['street_name']
            update_request_2.house_nr = unicode(long(a['house_nr']) + 1)
            update_request_2.bus_nr = a['house_bus']
            update_request_2.zip_code = a['zip_code']
            update_request_2.city = a['city']
            update_request_2.country_code = a['country_code']

            address_uid = update_profile_address(app_user, update_request_2).address_uid
            self.assertNotEqual(address_uid, a['address_uid'])
            upi = UserProfileInfo.create_key(app_user).get()
            tmp_upia = upi.get_address(address_uid)
            self.assertEqual(tmp_upia.label, update_request_2.label)
            self.assertEqual(tmp_upia.distance, update_request_2.distance)
            self.assertEqual(tmp_upia.house_nr, update_request_2.house_nr)
            profile_addresses = get_profile_addresses(app_user)
            self.assertEqual(len(profile_addresses), 1)

            delete_profile_addresses(app_user, [address_uid])
            address_uid = add_profile_address(app_user, add_request).address_uid
            profile_addresses = get_profile_addresses(app_user)
            self.assertEqual(len(profile_addresses), 1)

            s = setup_default_settings(app_user)
            self.assertEqual([u'be-testing-promo',
                              u'be-testing-promo-regional',
                              u'be-testing-city',
                              u'be-testing-traffic',
                              u'be-testing-events'], s.group_ids)

            if upia.address_uid not in address_hashes:
                address_hashes[upia.address_uid] = {'count': 0, 'items': []}
            if upia.street_uid not in street_hashes:
                street_hashes[upia.street_uid] = {'count': 0, 'items': []}

            address_hashes[upia.address_uid]['count'] += 1
            address_hashes[upia.address_uid]['items'].append(a)
            street_hashes[upia.street_uid]['count'] += 1
            street_hashes[upia.street_uid]['items'].append(a)

        address_hashes_sorted = sorted(address_hashes.values(), key=lambda x: -x['count'])
        street_hashes_sorted = sorted(street_hashes.values(), key=lambda x: -x['count'])

        return address_hashes_sorted, street_hashes_sorted

    def test_special_chars(self):
        addresses = [
            {
                u'city': u'Sint-Truiden',
                u'house_nr': u'1',
                u'street_name': u'Luci\u00ebndallaan',
                u'country_code': u'BE',
                u'house_bus': u'',
                u'zip_code': u'3800',
                u'geo': {
                    u'lat': 50.82824,
                    u'lng': 5.180919,
                    u'distance': 10000
                }
            }
        ]

        for i, a in enumerate(addresses):
            a['address_uid'] = UserProfileInfoAddress.create_uid(
                [a['country_code'], a['zip_code'], a['street_name'], a['house_nr'], a['house_bus']])
            a['street_uid'] = UserProfileInfoAddress.create_uid([a['country_code'], a['zip_code'], a['street_name']])

            app_user = users.User('user_chars_%s@example.com:%s' % (i, self.app_id))
            up = create_user_profile(app_user, app_user.email(), language=u'nl')
            up.birthdate = 0
            up.birth_day = UserProfile.get_birth_day_int(up.birthdate)
            up.gender = UserProfile.GENDER_MALE
            up.put()

            profile_addresses = get_profile_addresses(app_user)
            self.assertEqual(len(profile_addresses), 0)

            add_request = AddProfileAddressRequestTO()
            add_request.type = UserAddressType.WORK
            add_request.label = u"Work"
            add_request.geo_location = GeoPointTO()
            add_request.geo_location.lat = a['geo']['lat']
            add_request.geo_location.lon = a['geo']['lng']
            add_request.distance = a['geo']['distance']
            add_request.street_name = a['street_name']
            add_request.house_nr = a['house_nr']
            add_request.bus_nr = a['house_bus']
            add_request.zip_code = a['zip_code']
            add_request.city = a['city']
            add_request.country_code = a['country_code']

            address_uid = add_profile_address(app_user, add_request).address_uid
            self.assertEqual(address_uid, a['address_uid'])

            profile_addresses = get_profile_addresses(app_user)
            self.assertEqual(len(profile_addresses), 1)

    def test_news_locations(self):
        address_hashes_sorted, street_hashes_sorted = self._create_addresses()

        self.assertEqual(5, len(address_hashes_sorted))
        self.assertEqual(3, len(street_hashes_sorted))

        self.assertEqual(sum(s['count'] for s in street_hashes_sorted), UserProfileInfo.query().count())
        self.assertEqual(address_hashes_sorted[0]['count'], UserProfileInfo.list_by_address_uid(
            address_hashes_sorted[0]['items'][0]['address_uid']).count())
        self.assertEqual(street_hashes_sorted[0]['count'],
                         UserProfileInfo.list_by_street_uid(street_hashes_sorted[0]['items'][0]['street_uid']).count())

        ni1_lat = 51.092597
        ni1_lng = 3.8194548
        ni1_distance = 100

        l = []
        for a in address_hashes_sorted:
            for i in a['items']:
                l.append(long(haversine(i['geo']['lng'], i['geo']['lat'], ni1_lng, ni1_lat) * 1000))

        self.assertEqual(765, l[0])  # ACity BStreet 3
        self.assertEqual(17153, l[1])  # BCity AStreet 1
        self.assertEqual(765, l[2])  # ACity BStreet 1
        self.assertEqual(0, l[3])  # ACity AStreet 1
        self.assertEqual(0, l[4])  # ACity AStreet 3

        ni1_matches = []
        for a in address_hashes_sorted:
            for i in a['items']:
                ni1_matches.append(
                    should_match_location(ni1_lat, ni1_lng, ni1_distance, i['geo']['lat'], i['geo']['lng'],
                                          i['geo']['distance']))

        # Should match: ACity AStreet 1, ACity AStreet 3, ACity BStreet 3
        self.assertEqual([True, False, False, True, True], ni1_matches)

        ni2_lat = 51.0954861
        ni2_lng = 3.8293991
        ni2_distance = 100

        ni2_matches = []
        for a in address_hashes_sorted:
            for i in a['items']:
                ni2_matches.append(
                    should_match_location(ni2_lat, ni2_lng, ni2_distance, i['geo']['lat'], i['geo']['lng'],
                                          i['geo']['distance']))

        # Should match: ACity BStreet 1, ACity BStreet 3
        self.assertEqual([True, False, True, False, False], ni2_matches)

        ni3_lat = 51.0954861
        ni3_lng = 3.8293991
        ni3_distance = 300

        ni3_matches = []
        for a in address_hashes_sorted:
            for i in a['items']:
                ni3_matches.append(
                    should_match_location(ni3_lat, ni3_lng, ni3_distance, i['geo']['lat'], i['geo']['lng'],
                                          i['geo']['distance']))

        # Should match: ACity BStreet 1, ACity BStreet 3, ACity AStreet 3
        self.assertEqual([True, False, True, False, True], ni3_matches)

        with set_current_user(self.user, skip_create_session=True):
            news_item_0_to = self._create_news_item(1, app_ids=[self.app_id])
            news_item_0 = NewsItem.create_key(news_item_0_to.id).get()

            self.assertEqual(news_item_0.has_locations, False)
            self.assertEqual(news_item_0.location_match_required, False)
            self.assertIsNone(news_item_0.locations)
            self.assertEqual(news_item_0.group_types, [NewsGroup.TYPE_CITY])

            for i in range(5):
                app_user = users.User('user_%s@example.com:%s' % (i, self.app_id))
                s = NewsSettingsUser.create_key(app_user).get()

                @ndb.transactional
                def trans0():
                    return _create_news_item_match(s, news_item_0)

                t = trans0()
                self.assertIsNotNone(t)

            news_item_1_locations = NewsLocationsTO()
            news_item_1_locations.match_required = False
            news_item_1_locations.geo_addresses = [NewsGeoAddressTO(distance=ni3_distance,
                                                                    latitude=ni3_lat,
                                                                    longitude=ni3_lng)]
            news_item_1_locations.addresses = []

            news_item_1_to = self._create_news_item(1, locations=news_item_1_locations, app_ids=[self.app_id])
            news_item_1 = NewsItem.create_key(news_item_1_to.id).get()

            self.assertEqual(news_item_1.has_locations, True)
            self.assertEqual(news_item_1.location_match_required, False)
            self.assertEqual(len(news_item_1.locations.geo_addresses), 1)
            self.assertEqual(len(news_item_1.locations.addresses), 0)
            self.assertEqual(news_item_1.group_types, [NewsGroup.TYPE_CITY])
            self.assertEqual(news_item_1_to.group_type, NewsGroup.TYPE_CITY)

            for i in range(5):
                app_user = users.User('user_%s@example.com:%s' % (i, self.app_id))
                s = NewsSettingsUser.create_key(app_user).get()

                @ndb.transactional
                def trans1():
                    return _create_news_item_match(s, news_item_1)

                t = trans1()
                self.assertIsNotNone(t)
                m, _ = t
                if i in (0, 4):
                    self.assertEqual(m.group_ids, [u'be-testing-city'])
                    self.assertEqual(m.location_match, False)
                else:
                    self.assertEqual(m.group_ids, [u'be-testing-city'])
                    self.assertEqual(m.location_match, True)

            news_item_2_locations = NewsLocationsTO()
            news_item_2_locations.match_required = True
            news_item_2_locations.geo_addresses = []
            news_item_2_locations.addresses = [NewsAddressTO(level=NewsItemAddress.LEVEL_STREET,
                                                             country_code=u'BE',
                                                             city=u'ACity',
                                                             zip_code=u'AZipCode',
                                                             street_name=u'BStreet')]

            news_item_2_to = self._create_news_item(2, locations=news_item_2_locations, app_ids=[self.app_id],
                                                    group_type=NewsGroup.TYPE_EVENTS)
            news_item_2 = NewsItem.create_key(news_item_2_to.id).get()

            self.assertEqual(news_item_2.has_locations, True)
            self.assertEqual(news_item_2.location_match_required, True)
            self.assertEqual(len(news_item_2.locations.addresses), 1)
            self.assertEqual(len(news_item_2.locations.geo_addresses), 0)
            self.assertEqual(news_item_2.group_types, [NewsGroup.TYPE_EVENTS])
            self.assertEqual(news_item_2_to.group_type, NewsGroup.TYPE_EVENTS)

            for i in range(5):
                app_user = users.User('user_%s@example.com:%s' % (i, self.app_id))
                s = NewsSettingsUser.create_key(app_user).get()

                @ndb.transactional
                def trans2():
                    return _create_news_item_match(s, news_item_2)

                t = trans2()
                if i in (0, 1, 4):
                    self.assertIsNone(t)
                else:
                    self.assertIsNotNone(t)
                    m, _ = t
                    self.assertEqual(m.group_ids, [u'be-testing-events'])
                    self.assertEqual(m.location_match, True)

            news_item_3_locations = NewsLocationsTO()
            news_item_3_locations.match_required = True
            news_item_3_locations.geo_addresses = [NewsGeoAddressTO(distance=ni1_distance,
                                                                    latitude=ni1_lat,
                                                                    longitude=ni1_lng)]
            news_item_3_locations.addresses = [NewsAddressTO(level=NewsItemAddress.LEVEL_STREET,
                                                             country_code=u'BE',
                                                             city=u'ACity',
                                                             zip_code=u'AZipCode',
                                                             street_name=u'BStreet')]

            news_item_3_to = self._create_news_item(2, locations=news_item_3_locations, app_ids=[self.app_id],
                                                    group_type=NewsGroup.TYPE_EVENTS)
            news_item_3 = NewsItem.create_key(news_item_3_to.id).get()

            self.assertEqual(news_item_3.has_locations, True)
            self.assertEqual(news_item_3.location_match_required, True)
            self.assertEqual(len(news_item_3.locations.addresses), 1)
            self.assertEqual(len(news_item_3.locations.geo_addresses), 1)
            self.assertEqual(news_item_3.group_types, [NewsGroup.TYPE_EVENTS])
            self.assertEqual(news_item_3_to.group_type, NewsGroup.TYPE_EVENTS)

            for i in range(5):
                app_user = users.User('user_%s@example.com:%s' % (i, self.app_id))
                s = NewsSettingsUser.create_key(app_user).get()

                @ndb.transactional
                def trans3():
                    return _create_news_item_match(s, news_item_3)

                t = trans3()

                if i in (4,):
                    self.assertIsNone(t)
                else:
                    self.assertIsNotNone(t)
                    m, _ = t
                    self.assertEqual(m.group_ids, [u'be-testing-events'])
                    self.assertEqual(m.location_match, True)

        for i in range(5):
            app_user = users.User('user_%s@example.com:%s' % (i, self.app_id))
            r = get_groups_for_user(app_user)
            self.assertEqual(len(r.rows), 3)
