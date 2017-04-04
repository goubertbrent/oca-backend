# -*- coding: utf-8 -*-
# Copyright 2017 Mobicage NV
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
# @@license_version:1.3@@

from datetime import datetime, date
import json
import pytz

from babel.dates import format_date

from mcfw.properties import unicode_list_property, unicode_property, long_property, typed_property, bool_property, \
    long_list_property, object_factory, float_property
from mcfw.rpc import parse_complex_value
from rogerthat.to.service import UserDetailsTO
from rogerthat.utils import today
from rogerthat.utils.app import create_app_user_by_email
from solutions.common.bizz import _format_time, _format_date
from solutions.common.models.loyalty import SolutionLoyaltySettings


class LoyaltySlideNewOrderTO(object):
    app_id = unicode_property('1')
    url = unicode_property('2')
    full_url = unicode_property('3')
    time = long_property('5')
    content_type = unicode_property('6')

    @staticmethod
    def fromSlideObject(obj):
        to = LoyaltySlideNewOrderTO()
        to.app_id = obj.app_id
        to.full_url = obj.slide_url()
        to.url = obj.item_url()
        to.time = obj.time
        to.content_type = obj.content_type
        return to


class LoyaltySlideTO(object):
    id = long_property('1')
    url = unicode_property('2')
    full_url = unicode_property('3')
    name = unicode_property('4')
    time = long_property('5')
    content_type = unicode_property('6')
    str_apps = unicode_property('7')
    show_footer = bool_property('8')
    function_dependencies = long_property('9')

    @staticmethod
    def fromSolutionLoyaltySlideObject(obj, include_apps=False, show_footer=True):
        to = LoyaltySlideTO()
        to.id = obj.id
        to.full_url = obj.slide_url()
        to.url = obj.item_url()
        to.name = obj.name
        to.time = obj.time
        to.content_type = obj.content_type
        if include_apps:
            to.str_apps = unicode(obj.str_apps)
        else:
            to.str_apps = None
        to.show_footer = show_footer
        to.function_dependencies = obj.function_dependencies if obj.function_dependencies else 0
        return to

class LoyaltyRevenueDiscountSettingsTO(object):
    loyalty_type = SolutionLoyaltySettings.LOYALTY_TYPE_REVENUE_DISCOUNT

    x_visits = long_property('1')
    x_discount = long_property('2')

    @staticmethod
    def fromModel(obj):
        to = LoyaltyRevenueDiscountSettingsTO()
        to.x_visits = obj.x_visits if obj.x_visits else 10
        to.x_discount = obj.x_discount if obj.x_discount else 5
        return to

class LoyaltyLotterySettingsTO(object):
    loyalty_type = SolutionLoyaltySettings.LOYALTY_TYPE_LOTTERY

    @staticmethod
    def fromModel(obj):
        to = LoyaltyLotterySettingsTO()
        return to

class LoyaltyStampsSettingsTO(object):
    loyalty_type = SolutionLoyaltySettings.LOYALTY_TYPE_STAMPS
    x_stamps = long_property('1')
    stamps_type = long_property('2')
    stamps_winnings = unicode_property('3')
    stamps_auto_redeem = bool_property('4')

    @staticmethod
    def fromModel(obj):
        to = LoyaltyStampsSettingsTO()
        to.x_stamps = obj.x_stamps if obj.x_stamps else 8
        to.stamps_type = obj.stamps_type if obj.stamps_type else 1
        to.stamps_winnings = obj.stamps_winnings if obj.stamps_winnings else u""
        to.stamps_auto_redeem = obj.stamps_auto_redeem
        return to

class LoyaltyCityWideLotterySettingsTO(object):
    loyalty_type = SolutionLoyaltySettings.LOYALTY_TYPE_CITY_WIDE_LOTTERY

    @staticmethod
    def fromModel(obj):
        to = LoyaltyCityWideLotterySettingsTO()
        return to

LOYALTY_SETTINGS_MAPPING = {SolutionLoyaltySettings.LOYALTY_TYPE_REVENUE_DISCOUNT: LoyaltyRevenueDiscountSettingsTO,
                            SolutionLoyaltySettings.LOYALTY_TYPE_LOTTERY: LoyaltyLotterySettingsTO,
                            SolutionLoyaltySettings.LOYALTY_TYPE_STAMPS: LoyaltyStampsSettingsTO,
                            SolutionLoyaltySettings.LOYALTY_TYPE_CITY_WIDE_LOTTERY: LoyaltyCityWideLotterySettingsTO}

class LoyaltySettingsTO(object):
    image_uri = unicode_property('1')
    admins = unicode_list_property('2')
    names = unicode_list_property('3')
    functions = long_list_property('4')
    loyalty_type = long_property('7')
    loyalty_settings = typed_property('8', object_factory('loyalty_type', LOYALTY_SETTINGS_MAPPING), False)
    loyalty_website = unicode_property('9')

    @staticmethod
    def fromSolutionLoyaltySettingsObject(sln_l_settings, sln_li_settings, loyalty_type=None):
        to = LoyaltySettingsTO()
        to.image_uri = sln_li_settings.image_uri
        to.admins = [create_app_user_by_email(admin, app_id).email() for (admin, app_id) in zip(sln_li_settings.admins, sln_li_settings.app_ids)]
        to.names = sln_li_settings.names
        to.functions = sln_li_settings.functions
        if not loyalty_type:
            loyalty_type = sln_l_settings.loyalty_type
        to.loyalty_type = loyalty_type
        to.loyalty_settings = LOYALTY_SETTINGS_MAPPING[loyalty_type].fromModel(sln_l_settings)
        to.loyalty_website = sln_l_settings.website
        return to


class SolutionLoyaltyVisitTO(object):
    key = unicode_property('1')
    loyalty_type = long_property('2')
    timestamp = long_property('3')
    value_number = long_property('4')
    timestamp_day = long_property('5')

    @staticmethod
    def fromModel(obj):
        to = SolutionLoyaltyVisitTO()
        to.key = obj.key_str.decode('utf8')
        to.loyalty_type = obj.loyalty_type
        to.timestamp = obj.timestamp
        if obj.loyalty_type == SolutionLoyaltySettings.LOYALTY_TYPE_REVENUE_DISCOUNT:
            to.value_number = obj.price
            to.timestamp_day = to.timestamp - (to.timestamp % (3600 * 24))
        elif obj.loyalty_type == SolutionLoyaltySettings.LOYALTY_TYPE_LOTTERY:
            to.value_number = 1
            to.timestamp_day = obj.timestamp_day
        elif obj.loyalty_type == SolutionLoyaltySettings.LOYALTY_TYPE_STAMPS:
            to.value_number = obj.count
            to.timestamp_day = to.timestamp - (to.timestamp % (3600 * 24))
        else:
            to.timestamp_day = 0
            to.value_number = 0
        return to


class ExtendedUserDetailsTO(UserDetailsTO):
    app_name = unicode_property('51')

    @classmethod
    def fromUserProfile(cls, user_profile, app_name):
        to = super(ExtendedUserDetailsTO, cls).fromUserProfile(user_profile)
        to.app_name = app_name
        return to

class LoyaltyCustomerPointsTO(object):
    user_details = typed_property('1', ExtendedUserDetailsTO, False)
    visits = typed_property('2', SolutionLoyaltyVisitTO, True)

class BaseLoyaltyCustomersTO(object):
    loyalty_type = long_property('1')
    customers = typed_property('2', LoyaltyCustomerPointsTO, True)
    cursor = unicode_property('3')
    has_more = bool_property('4')

class LoyaltyCustomersTO(BaseLoyaltyCustomersTO):
    loyalty_settings = typed_property('10', object_factory('loyalty_type', LOYALTY_SETTINGS_MAPPING), False)

class CustomerSavedPointsTO(object):
    loyalty_type = long_property('1')
    user_details = typed_property('2', ExtendedUserDetailsTO, False)
    total_spent = long_property('3')  # in cents
    tmp_discount = long_property('4')  # in cents
    visit_count = long_property('5')


class LoyaltyScanTO(object):
    key = unicode_property('1')
    tablet_name = unicode_property('2')
    user_name = unicode_property('3')
    timestamp = long_property('4')
    date = unicode_property('5')
    points = typed_property('6', CustomerSavedPointsTO, False)
    loyalty_type = long_property('7')
    loyalty_settings = typed_property('8', object_factory('loyalty_type', LOYALTY_SETTINGS_MAPPING), False)

    @staticmethod
    def fromSolutionLoyaltyScanObject(obj, loyalty_settings, sln_settings, visits=None):
        from rogerthat.dal.profile import get_profile_info
        from solutions.common.bizz import get_app_info_cached

        to = LoyaltyScanTO()
        to.key = unicode(obj.key_str)
        to.tablet_name = obj.tablet_name
        to.user_name = obj.user_name
        to.timestamp = obj.timestamp

        today_ = today()
        timestamp_day = obj.timestamp - (obj.timestamp % (3600 * 24))
        date_sent = datetime.fromtimestamp(obj.timestamp, pytz.timezone(sln_settings.timezone))
        time_ = _format_time(sln_settings.main_language, date_sent)
        if today_ == timestamp_day:
            to.date = unicode(time_)
        else:
            to.date = unicode("%s %s" % (_format_date(sln_settings.main_language, date_sent), time_))

        saved_points = CustomerSavedPointsTO()
        saved_points.loyalty_type = loyalty_settings.loyalty_type
        saved_points.total_spent = 0
        saved_points.tmp_discount = 0
        saved_points.visit_count = 0
        # XXX: don't use get_profile_infos
        profile_info = get_profile_info(obj.app_user)
        saved_points.user_details = ExtendedUserDetailsTO.fromUserProfile(profile_info)
        app_info = get_app_info_cached(saved_points.user_details.app_id)
        saved_points.user_details.app_name = app_info.name

        if loyalty_settings.loyalty_type == SolutionLoyaltySettings.LOYALTY_TYPE_REVENUE_DISCOUNT:
            x_discount = 5 if loyalty_settings.x_discount is None else loyalty_settings.x_discount
            if visits:
                for visit in visits:
                    saved_points.total_spent += visit.price
                    saved_points.visit_count += 1
                    saved_points.tmp_discount = long(saved_points.total_spent * x_discount / 100)

        elif loyalty_settings.loyalty_type == SolutionLoyaltySettings.LOYALTY_TYPE_STAMPS:
            if visits:
                for visit in visits:
                    saved_points.total_spent += visit.count
                    saved_points.visit_count += 1

        to.points = saved_points

        to.loyalty_type = loyalty_settings.loyalty_type
        if loyalty_settings.loyalty_type == SolutionLoyaltySettings.LOYALTY_TYPE_REVENUE_DISCOUNT:
            to.loyalty_settings = LoyaltyRevenueDiscountSettingsTO.fromModel(loyalty_settings)
        elif loyalty_settings.loyalty_type == SolutionLoyaltySettings.LOYALTY_TYPE_STAMPS:
            to.loyalty_settings = LoyaltyStampsSettingsTO.fromModel(loyalty_settings)
        return to

class LoyaltyLotteryInfoTO(object):
    key = unicode_property('1')
    timestamp = long_property('2')
    end_timestamp = long_property('3')
    winnings = unicode_property('4')
    winner_timestamp = long_property('5')
    winners = typed_property('6', ExtendedUserDetailsTO, True)
    redeemed = bool_property('7')
    claimed = bool_property('8')
    next_winner_timestamp = long_property('9')
    x_winners = long_property('10')

    @staticmethod
    def fromModel(obj):
        to = LoyaltyLotteryInfoTO()
        to.key = unicode(obj.key_str)
        to.timestamp = obj.timestamp
        to.end_timestamp = obj.end_timestamp
        to.winnings = obj.winnings
        to.winner_timestamp = obj.winner_timestamp
        to.winners = []
        if obj.winner_info:
            from solutions.common.bizz import get_app_info_cached
            eud = ExtendedUserDetailsTO()
            eud.name = obj.winner_info.name
            eud.avatar_url = obj.winner_info.avatar_url
            eud.language = obj.winner_info.language
            eud.email = obj.winner_info.email
            eud.app_id = obj.winner_info.app_id
            eud.public_key = None
            app_info = get_app_info_cached(obj.winner_info.app_id)
            eud.app_name = app_info.name
            to.winners.append(eud)
        to.redeemed = obj.redeemed
        to.claimed = obj.claimed
        to.next_winner_timestamp = obj.winner_timestamp + (24 * 3600)
        to.x_winners = 1
        return to

class CityWideLotteryInfoTO(object):
    key = unicode_property('1')
    timestamp = long_property('2')
    end_timestamp = long_property('3')
    winnings = unicode_property('4')
    winners = typed_property('5', ExtendedUserDetailsTO, True)
    redeemed = bool_property('6')
    claimed = bool_property('7')
    x_winners = long_property('8')

    @staticmethod
    def fromModel(obj):
        to = CityWideLotteryInfoTO()
        to.key = unicode(obj.key_str)
        to.timestamp = obj.timestamp
        to.end_timestamp = obj.end_timestamp
        to.winnings = obj.winnings

        if obj.winners_info:
            to.winners = parse_complex_value(ExtendedUserDetailsTO, json.loads(obj.winners_info), True)
            to.redeemed = True
            to.claimed = True
        else:
            to.winners = []
            to.redeemed = False
            to.claimed = False
        to.x_winners = obj.x_winners
        return to

class LoyaltyLotteryChanceTO(object):
    total_visits = long_property('1')
    my_visits = long_property('2')
    chance = float_property('3')


class SolutionLoyaltyExportTO(object):
    month = long_property('1')
    month_str = unicode_property('2')
    year = long_property('3')

    @classmethod
    def from_model(cls, model, language):
        to = cls()
        to.month = int(str(model.year_month)[4:])
        to.year = int(str(model.year_month)[0:4])
        d = date(to.year, to.month, 1)
        to.month_str = format_date(d, format='MMMM', locale=language)
        return to


class SolutionLoyaltyExportListTO(object):
    cursor = unicode_property('1')
    list = typed_property('2', SolutionLoyaltyExportTO, True)

    @classmethod
    def create(cls, cursor, list_):
        to = cls()
        to.cursor = cursor
        to.list = list_
        return to
