# -*- coding: utf-8 -*-
# Copyright 2017 GIG Technology NV
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

import logging
from types import NoneType

from google.appengine.ext import blobstore, db

from mcfw.consts import MISSING
from mcfw.properties import object_factory
from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.dal import put_and_invalidate_cache, parent_key_unsafe
from rogerthat.dal.profile import get_profile_infos
from rogerthat.rpc import users
from rogerthat.rpc.service import BusinessException
from rogerthat.to import ReturnStatusTO, RETURNSTATUS_TO_SUCCESS
from rogerthat.to.service import UserDetailsTO
from rogerthat.utils import now, replace_url_with_forwarded_server
from rogerthat.utils.app import create_app_user_by_email
from rogerthat.utils.channel import send_message
from solutions import translate as common_translate
from solutions.common import SOLUTION_COMMON
from solutions.common.bizz import loyalty as loyalty_bizz, broadcast_updates_pending, get_app_info_cached, \
    SolutionModule
from solutions.common.bizz.loyalty import add_loyalty_for_user, redeem_loyalty_for_user, calculate_chance_for_user, \
    delete_visit, request_loyalty_device, calculate_city_wide_lottery_chance_for_user
from solutions.common.dal import get_solution_settings
from solutions.common.dal.loyalty import get_solution_loyalty_slides, get_solution_loyalty_visits_for_revenue_discount, \
    get_solution_loyalty_visits_for_lottery, get_solution_loyalty_visits_for_stamps, \
    get_solution_city_wide_lottery_loyalty_visits_for_user
from solutions.common.models import SolutionSettings
from solutions.common.models.loyalty import SolutionLoyaltySettings, SolutionLoyaltyScan, SolutionLoyaltyLottery, \
    SolutionLoyaltyExport, SolutionLoyaltyIdentitySettings, SolutionCityWideLotteryVisit, SolutionCityWideLottery
from solutions.common.to import TimestampTO
from solutions.common.to.loyalty import LoyaltySettingsTO, LoyaltySlideTO, ExtendedUserDetailsTO, \
    LoyaltyScanTO, LOYALTY_SETTINGS_MAPPING, SolutionLoyaltyVisitTO, LoyaltyRevenueDiscountSettingsTO, \
    LoyaltyLotterySettingsTO, LoyaltyCustomersTO, LoyaltyCustomerPointsTO, LoyaltyLotteryInfoTO, LoyaltyLotteryChanceTO, \
    LoyaltyStampsSettingsTO, SolutionLoyaltyExportTO, SolutionLoyaltyExportListTO, BaseLoyaltyCustomersTO, \
    CityWideLotteryInfoTO, LoyaltyCityWideLotterySettingsTO
from solutions.common.utils import is_default_service_identity, create_service_identity_user_wo_default


@rest("/common/loyalty/slides/get_upload_url", "get", read_only_access=True)
@returns(unicode)
@arguments()
def get_upload_url_item():
    upload_url = blobstore.create_upload_url('/common/loyalty/slide/upload')
    return replace_url_with_forwarded_server(upload_url)

@rest("/common/loyalty/slides/load", "get", read_only_access=True)
@returns([LoyaltySlideTO])
@arguments()
def load_loyalty_slides():
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    return [LoyaltySlideTO.fromSolutionLoyaltySlideObject(c) for c in get_solution_loyalty_slides(service_user, service_identity)]

@rest("/common/loyalty/slides/delete", "post")
@returns(ReturnStatusTO)
@arguments(slide_id=(int, long))
def delete_loyalty_slide(slide_id):
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    try:
        loyalty_bizz.delete_loyalty_slide(service_user, service_identity, slide_id)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException, e:
        return ReturnStatusTO.create(False, e.message)


@rest("/common/loyalty/settings/load", "get", read_only_access=True)
@returns(LoyaltySettingsTO)
@arguments()
def load_loyalty_settings():
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    def trans():
        sln_l_settings = SolutionLoyaltySettings.get_by_user(service_user)
        if is_default_service_identity(service_identity):
            sln_li_settings = sln_l_settings
        else:
            sln_li_settings = SolutionLoyaltyIdentitySettings.get_by_user(service_user, service_identity)
        return sln_l_settings, sln_li_settings
    xg_on = db.create_transaction_options(xg=True)
    sln_l_settings, sln_li_settings = db.run_in_transaction_options(xg_on, trans)
    return LoyaltySettingsTO.fromSolutionLoyaltySettingsObject(sln_l_settings, sln_li_settings) if sln_l_settings else None


@rest("/common/loyalty/settings/load_specific", "get", read_only_access=True)
@returns(LoyaltySettingsTO)
@arguments(loyalty_type=(int, long))
def load_specific_loyalty_settings(loyalty_type):
    service_user = users.get_current_user()
    # only a shop user can load a specific loyalty type
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    sln_settings = get_solution_settings(service_user)
    if SolutionModule.HIDDEN_CITY_WIDE_LOTTERY in sln_settings.modules:
        loyalty_type = None
    def trans():
        sln_l_settings = SolutionLoyaltySettings.get_by_user(service_user)
        if is_default_service_identity(service_identity):
            sln_li_settings = sln_l_settings
        else:
            sln_li_settings = SolutionLoyaltyIdentitySettings.get_by_user(service_user, service_identity)
        return sln_l_settings, sln_li_settings
    xg_on = db.create_transaction_options(xg=True)
    sln_l_settings, sln_li_settings = db.run_in_transaction_options(xg_on, trans)
    return LoyaltySettingsTO.fromSolutionLoyaltySettingsObject(sln_l_settings, sln_li_settings, loyalty_type if session_.shop else None) if sln_l_settings else None

@rest("/common/loyalty/settings/put", "post")
@returns(ReturnStatusTO)
@arguments(loyalty_type=(int, long), loyalty_settings=object_factory("loyalty_type", LOYALTY_SETTINGS_MAPPING), loyalty_website=unicode)
def put_loyalty_settings(loyalty_type, loyalty_settings, loyalty_website):
    service_user = users.get_current_user()
    # only a shop user can update the loyalty type
    session_ = users.get_current_session()
    try:
        def trans(loyalty_type):
            sln_settings = get_solution_settings(service_user)
            if SolutionModule.HIDDEN_CITY_WIDE_LOTTERY in sln_settings.modules:
                loyalty_type = SolutionLoyaltySettings.LOYALTY_TYPE_CITY_WIDE_LOTTERY
            sln_settings.updates_pending = True

            sln_loyalty_settings = SolutionLoyaltySettings.get_by_user(service_user)

            if sln_loyalty_settings.loyalty_type != loyalty_type:
                sln_loyalty_settings.branding_key = None
                sln_settings.loyalty_branding_hash = None

            if sln_loyalty_settings.website != loyalty_website:
                sln_loyalty_settings.modification_time = now()

            sln_loyalty_settings.website = loyalty_website

            if loyalty_type == SolutionLoyaltySettings.LOYALTY_TYPE_REVENUE_DISCOUNT:
                sln_loyalty_settings.x_visits = loyalty_settings.x_visits
                sln_loyalty_settings.x_discount = loyalty_settings.x_discount
            elif loyalty_type == SolutionLoyaltySettings.LOYALTY_TYPE_STAMPS:
                sln_loyalty_settings.x_stamps = loyalty_settings.x_stamps
                sln_loyalty_settings.stamps_type = loyalty_settings.stamps_type
                sln_loyalty_settings.stamps_winnings = loyalty_settings.stamps_winnings
                sln_loyalty_settings.stamps_auto_redeem = loyalty_settings.stamps_auto_redeem

            if session_.shop:
                sln_loyalty_settings.loyalty_type = loyalty_type

            put_and_invalidate_cache(sln_loyalty_settings, sln_settings)
            return sln_settings

        xg_on = db.create_transaction_options(xg=True)
        sln_settings = db.run_in_transaction_options(xg_on, trans, loyalty_type)
        broadcast_updates_pending(sln_settings)

        send_message(service_user, u"solutions.common.loyalty.settings.update")
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException, e:
        return ReturnStatusTO.create(False, e.message)

@rest("/common/loyalty/settings/admin/delete", "post")
@returns(ReturnStatusTO)
@arguments(admin_app_user_email=unicode)
def delete_loyalty_admin(admin_app_user_email):
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    try:
        loyalty_bizz.delete_loyalty_admin(service_user, service_identity, admin_app_user_email)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException, e:
        return ReturnStatusTO.create(False, e.message)

@rest("/common/loyalty/settings/admin/update", "post")
@returns(ReturnStatusTO)
@arguments(admin_app_user_email=unicode, admin_name=unicode, admin_functions=(int, long))
def update_loyalty_admin(admin_app_user_email, admin_name, admin_functions):
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    try:
        loyalty_bizz.update_loyalty_admin(service_user, service_identity, admin_app_user_email, admin_name, admin_functions)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException, e:
        return ReturnStatusTO.create(False, e.message)


@rest("/common/loyalty/customer_points/load", "get", read_only_access=True)
@returns(LoyaltyCustomersTO)
@arguments(loyalty_type=(int, long, NoneType), cursor=unicode)
def load_customer_points(loyalty_type=None, cursor=None):
    service_user = users.get_current_user()
    # only a shop user can load points of a specific loyalty type
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    if not session_.shop:
        loyalty_type = None
    loyalty_settings = SolutionLoyaltySettings.get_by_user(service_user)
    if not loyalty_type:
        loyalty_type = loyalty_settings.loyalty_type
    result_dict = dict()
    visits = []
    cursor_ = None
    has_more = False
    if loyalty_type in SolutionLoyaltySettings.LOYALTY_TYPE_MAPPING:
        qry = SolutionLoyaltySettings.LOYALTY_TYPE_MAPPING[loyalty_type].load(service_user, service_identity)
        qry.with_cursor(cursor)
        visits = qry.fetch(10)
        cursor_ = qry.cursor()
        if len(visits) != 0:
            qry.with_cursor(cursor_)
            if len(qry.fetch(1)) > 0:
                has_more = True

    for visit in visits:
        saved_points = result_dict.get(visit.app_user)
        if not saved_points:
            result_dict[visit.app_user] = saved_points = LoyaltyCustomerPointsTO()
            saved_points.visits = []

        saved_points.visits.append(SolutionLoyaltyVisitTO.fromModel(visit))

    # XXX: don't use get_profile_infos
    app_users = result_dict.keys()
    profile_infos = get_profile_infos(app_users, allow_none_in_results=True)
    for app_user, profile_info in zip(app_users, profile_infos):
        if not profile_info or profile_info.isServiceIdentity:
            logging.info('User %s not found', app_user.email())
            del result_dict[app_user]
            continue
        saved_points = result_dict[app_user]
        saved_points.user_details = ExtendedUserDetailsTO.fromUserProfile(profile_info, None)
        app_info = get_app_info_cached(saved_points.user_details.app_id)
        saved_points.user_details.app_name = app_info.name
        saved_points.visits = sorted(saved_points.visits,
                                     key=lambda x:-x.timestamp)

    r = LoyaltyCustomersTO()
    r.cursor = cursor_.decode("utf8") if cursor_ else None
    r.has_more = has_more
    r.loyalty_type = loyalty_type
    if loyalty_type == SolutionLoyaltySettings.LOYALTY_TYPE_REVENUE_DISCOUNT:
        r.loyalty_settings = LoyaltyRevenueDiscountSettingsTO.fromModel(loyalty_settings)
    elif loyalty_type == SolutionLoyaltySettings.LOYALTY_TYPE_LOTTERY:
        r.loyalty_settings = LoyaltyLotterySettingsTO.fromModel(loyalty_settings)
    elif loyalty_type == SolutionLoyaltySettings.LOYALTY_TYPE_STAMPS:
        r.loyalty_settings = LoyaltyStampsSettingsTO.fromModel(loyalty_settings)
    elif loyalty_type == SolutionLoyaltySettings.LOYALTY_TYPE_CITY_WIDE_LOTTERY:
        r.loyalty_settings = LoyaltyCityWideLotterySettingsTO.fromModel(loyalty_settings)
    else:
        r.loyalty_settings = None
    r.customers = sorted(result_dict.itervalues(),
                    key=lambda x:-x.visits[0].timestamp)

    return r

@rest("/common/loyalty/visit/delete", "post")
@returns(ReturnStatusTO)
@arguments(key=unicode)
def delete_loyalty_visit(key):
    service_user = users.get_current_user()
    try:
        delete_visit(service_user, key)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException, e:
        sln_settings = get_solution_settings(service_user)
        return ReturnStatusTO.create(False, common_translate(sln_settings.main_language, SOLUTION_COMMON, e.message))


@rest("/common/loyalty/customer_points/detail", "get", read_only_access=True)
@returns(LoyaltyCustomerPointsTO)
@arguments(loyalty_type=(int, long), email=unicode, app_id=unicode)
def load_detail_customer_points(loyalty_type, email, app_id):
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    app_user = create_app_user_by_email(email, app_id)
    if loyalty_type == SolutionLoyaltySettings.LOYALTY_TYPE_REVENUE_DISCOUNT:
        visits = get_solution_loyalty_visits_for_revenue_discount(service_user, service_identity, app_user)
    elif loyalty_type == SolutionLoyaltySettings.LOYALTY_TYPE_LOTTERY:
        visits = get_solution_loyalty_visits_for_lottery(service_user, service_identity, app_user)
    else:
        visits = get_solution_loyalty_visits_for_stamps(service_user, service_identity, app_user)

    r = LoyaltyCustomerPointsTO()


    # XXX: don't use get_profile_infos
    profile_infos = get_profile_infos([app_user], allow_none_in_results=True)
    for app_user, profile_info in zip([app_user], profile_infos):
        if not profile_info or profile_info.isServiceIdentity:
            continue
        r.user_details = ExtendedUserDetailsTO.fromUserProfile(profile_info, None)
        app_info = get_app_info_cached(r.user_details.app_id)
        r.user_details.app_name = app_info.name
    r.visits = [SolutionLoyaltyVisitTO.fromModel(visit) for visit in visits]
    return r

@rest("/common/loyalty/lottery/chance", "get", read_only_access=True)
@returns(LoyaltyLotteryChanceTO)
@arguments(email=unicode, app_id=unicode)
def load_chance_user(email, app_id):
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    app_user = create_app_user_by_email(email, app_id)
    r = LoyaltyLotteryChanceTO()
    r.total_visits, r.my_visits, r.chance = calculate_chance_for_user(service_user, service_identity, app_user)
    return r


@rest("/common/loyalty/scans/load", "get", read_only_access=True)
@returns([LoyaltyScanTO])
@arguments()
def load_loyalty_scans():
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    sln_settings = get_solution_settings(service_user)
    loyalty_settings = SolutionLoyaltySettings.get_by_user(service_user)
    loyalty_scans = SolutionLoyaltyScan.get_by_service_user(service_user, service_identity)
    r = []
    for c in loyalty_scans:
        visits = []
        if loyalty_settings.loyalty_type == SolutionLoyaltySettings.LOYALTY_TYPE_REVENUE_DISCOUNT:
            visits = get_solution_loyalty_visits_for_revenue_discount(c.service_user, c.service_identity, c.app_user, loyalty_settings.x_visits)
        else:
            visits = get_solution_loyalty_visits_for_stamps(c.service_user, c.service_identity, c.app_user, loyalty_settings.x_stamps)
        r.append(LoyaltyScanTO.fromSolutionLoyaltyScanObject(c, loyalty_settings, sln_settings, visits))
    return r



@rest("/common/loyalty/scans/add", "post")
@returns(ReturnStatusTO)
@arguments(key=unicode, loyalty_type=(int, long), value=(int, long))
def add_loyalty_scan(key, loyalty_type, value):
    service_user = users.get_current_user()
    try:
        sls = SolutionLoyaltyScan.get(key)
        if sls is None:
            raise BusinessException("Could not find scan")
        if sls.processed:
            raise BusinessException("Scan was already processed")

        if sls.app_user_info:
            user_details = UserDetailsTO()
            user_details.email = sls.app_user_info.email
            user_details.name = sls.app_user_info.name
            user_details.language = sls.app_user_info.language
            user_details.avatar_url = sls.app_user_info.avatar_url
            user_details.app_id = sls.app_user_info.app_id
        else:
            # XXX: don't use get_profile_infos
            profile_info = get_profile_infos([sls.app_user], allow_none_in_results=True)[0]
            if not profile_info or profile_info.isServiceIdentity:
                user_details = None
            else:
                user_details = UserDetailsTO.fromUserProfile(profile_info)

        jsondata = {}
        jsondata['loyalty_type'] = loyalty_type
        if loyalty_type == SolutionLoyaltySettings.LOYALTY_TYPE_REVENUE_DISCOUNT:
            jsondata['price'] = value
        else:
            jsondata['count'] = value
        success, _, _ = add_loyalty_for_user(service_user, sls.service_identity, sls.admin_user, sls.app_user, jsondata, now(), user_details)
        if not success:
            raise BusinessException("error-occured-unknown")

        sls.processed = True
        sls.put()
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException, e:
        sln_settings = get_solution_settings(service_user)
        return ReturnStatusTO.create(False, common_translate(sln_settings.main_language, SOLUTION_COMMON, e.message))


@rest("/common/loyalty/scans/redeem", "post")
@returns(ReturnStatusTO)
@arguments(key=unicode, loyalty_type=(int, long), value=(int, long))
def redeem_loyalty_scan(key, loyalty_type, value):
    service_user = users.get_current_user()
    try:
        sls = SolutionLoyaltyScan.get(key)
        if sls is None:
            raise BusinessException("Could not find scan")
        if sls.processed:
            raise BusinessException("Scan was already processed")

        jsondata = {}
        jsondata['loyalty_type'] = loyalty_type
        if loyalty_type == SolutionLoyaltySettings.LOYALTY_TYPE_STAMPS:
            jsondata['count'] = value
        success = redeem_loyalty_for_user(service_user, sls.service_identity, sls.admin_user, sls.app_user, jsondata)
        if not success:
            raise BusinessException("error-occured-unknown")
        sls.processed = True
        sls.put()
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException, e:
        sln_settings = get_solution_settings(service_user)
        return ReturnStatusTO.create(False, common_translate(sln_settings.main_language, SOLUTION_COMMON, e.message))


@rest("/common/loyalty/lottery/add", "post")
@returns(ReturnStatusTO)
@arguments(winnings=unicode, date=TimestampTO)
def add_loyalty_lottery_info(winnings, date):
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    sln_settings = get_solution_settings(service_user)
    try:
        now_ = now()
        end_timestamp = date.toEpoch()
        if end_timestamp <= (now_ + 24 * 3600):
            raise BusinessException("end-date-24h-in-future")

        ll_info = SolutionLoyaltyLottery.load_pending(service_user, service_identity)
        if ll_info:
            if end_timestamp <= ll_info.end_timestamp:
                raise BusinessException("lottery-time-bigger-first-upcoming")

        service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
        ll_info = SolutionLoyaltyLottery(parent=parent_key_unsafe(service_identity_user, SOLUTION_COMMON))
        ll_info.timestamp = now_
        ll_info.end_timestamp = end_timestamp
        ll_info.schedule_loot_time = ll_info.end_timestamp - 24 * 3600
        ll_info.winnings = winnings
        ll_info.winner = None
        ll_info.winner_info = None
        ll_info.winner_timestamp = 0
        ll_info.skip_winners = []
        ll_info.pending = True
        ll_info.redeemed = False
        ll_info.claimed = False
        ll_info.put()

        sln_settings.updates_pending = True
        put_and_invalidate_cache(sln_settings)
        broadcast_updates_pending(sln_settings)

        send_message(service_user, u"solutions.common.loyalty.lottery.update", service_identity=service_identity)

        return RETURNSTATUS_TO_SUCCESS
    except BusinessException, e:
        return ReturnStatusTO.create(False, common_translate(sln_settings.main_language, SOLUTION_COMMON, e.message))


@rest("/common/loyalty/lottery/edit", "post")
@returns(ReturnStatusTO)
@arguments(key=unicode, winnings=unicode, date=TimestampTO)
def edit_loyalty_lottery_info(key, winnings, date):
    ll_info_edit = SolutionLoyaltyLottery.get(key)
    if not ll_info_edit:
        return RETURNSTATUS_TO_SUCCESS

    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    sln_settings = get_solution_settings(service_user)

    try:
        now_ = now()
        end_timestamp = date.toEpoch()
        if end_timestamp <= (now_ + 24 * 3600):
            raise BusinessException("end-date-24h-in-future")

        ll_info = SolutionLoyaltyLottery.load_pending(service_user, service_identity)
        if ll_info_edit.key() != ll_info.key() and end_timestamp <= ll_info.end_timestamp:
            raise BusinessException("lottery-time-bigger-first-upcoming")

        ll_info_edit.end_timestamp = end_timestamp
        ll_info_edit.schedule_loot_time = ll_info_edit.end_timestamp - 24 * 3600
        ll_info_edit.winnings = winnings
        ll_info_edit.put()

        sln_settings.updates_pending = True
        put_and_invalidate_cache(sln_settings)
        broadcast_updates_pending(sln_settings)

        send_message(service_user, u"solutions.common.loyalty.lottery.update", service_identity=service_identity)

        return RETURNSTATUS_TO_SUCCESS
    except BusinessException, e:
        return ReturnStatusTO.create(False, common_translate(sln_settings.main_language, SOLUTION_COMMON, e.message))


@rest("/common/loyalty/lottery/delete", "post")
@returns(ReturnStatusTO)
@arguments(key=unicode)
def delete_loyalty_lottery_info(key):
    ll_info_delete = SolutionLoyaltyLottery.get(key)
    if not ll_info_delete:
        return RETURNSTATUS_TO_SUCCESS

    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    sln_settings = get_solution_settings(service_user)

    try:
        ll_info = SolutionLoyaltyLottery.load_pending(service_user, service_identity)
        if ll_info_delete.key() == ll_info.key():
            raise RETURNSTATUS_TO_SUCCESS
        if ll_info_delete.schedule_loot_time > 0:
            ll_info_delete.delete()

        sln_settings.updates_pending = True
        put_and_invalidate_cache(sln_settings)
        broadcast_updates_pending(sln_settings)

        send_message(service_user, u"solutions.common.loyalty.lottery.update", service_identity=service_identity)

        return RETURNSTATUS_TO_SUCCESS
    except BusinessException, e:
        return ReturnStatusTO.create(False, common_translate(sln_settings.main_language, SOLUTION_COMMON, e.message))


@rest("/common/loyalty/lottery/close", "post")
@returns(ReturnStatusTO)
@arguments(key=unicode)
def close_loyalty_lottery_info(key):
    service_user = users.get_current_user()
    try:
        ll_info = SolutionLoyaltyLottery.get(key)
        if ll_info and ll_info.redeemed and not ll_info.deleted:
            ll_info.deleted = True
            ll_info.put()

        send_message(service_user, u"solutions.common.loyalty.lottery.update", service_identity=ll_info.service_identity)

        return RETURNSTATUS_TO_SUCCESS
    except BusinessException, e:
        sln_settings = get_solution_settings(service_user)
        return ReturnStatusTO.create(False, common_translate(sln_settings.main_language, SOLUTION_COMMON, e.message))

@rest("/common/loyalty/lottery/load", "get", read_only_access=True)
@returns([LoyaltyLotteryInfoTO])
@arguments()
def load_loyalty_lottery_info():
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    return [LoyaltyLotteryInfoTO.fromModel(ll_info) for ll_info in SolutionLoyaltyLottery.load_all(service_user, service_identity)]


@rest("/common/loyalty/export/list", "get", read_only_access=True)
@returns(SolutionLoyaltyExportListTO)
@arguments(cursor=unicode)
def load_loyalty_export_list(cursor=None):
    service_user = users.get_current_user()
    session_ = users.get_current_session()
    service_identity = session_.service_identity
    sln_settings = SolutionSettings.get(SolutionSettings.create_key(service_user))
    exports_q = SolutionLoyaltyExport.list_by_service_user(service_user, service_identity)
    exports_q.with_cursor(cursor)
    exports_list = exports_q.fetch(10)
    cursor = unicode(exports_q.cursor())
    to = SolutionLoyaltyExportListTO.create(cursor,
                                            [SolutionLoyaltyExportTO.from_model(e, sln_settings.main_language)
                                             for e in exports_list])
    return to


@rest('/common/loyalty/request_device', 'get')
@returns(ReturnStatusTO)
@arguments(source=unicode)
def rest_request_loyalty_device(source=MISSING):
    try:
        request_loyalty_device(users.get_current_user(), source if source is not MISSING else None)
        return RETURNSTATUS_TO_SUCCESS
    except BusinessException, exception:
        return ReturnStatusTO.create(False, exception.message)


@rest("/common/city_wide_lottery/customer_points/load", "get", read_only_access=True)
@returns(BaseLoyaltyCustomersTO)
@arguments(city_app_id=unicode, cursor=unicode)
def load_city_wide_lottery_customer_points(city_app_id, cursor=None):

    result_dict = dict()
    qry = SolutionCityWideLotteryVisit.load(city_app_id)
    qry.with_cursor(cursor)
    visits = qry.fetch(10)
    cursor_ = qry.cursor()
    has_more = False
    if len(visits) != 0:
        qry.with_cursor(cursor_)
        if len(qry.fetch(1)) > 0:
            has_more = True

    for visit in visits:
        saved_points = result_dict.get(visit.app_user)
        if not saved_points:
            result_dict[visit.app_user] = saved_points = LoyaltyCustomerPointsTO()
            saved_points.visits = []

        saved_points.visits.append(SolutionLoyaltyVisitTO.fromModel(visit))

    # XXX: don't use get_profile_infos
    app_users = result_dict.keys()
    profile_infos = get_profile_infos(app_users, allow_none_in_results=True)
    for app_user, profile_info in zip(app_users, profile_infos):
        if not profile_info or profile_info.isServiceIdentity:
            logging.info('User %s not found', app_user.email())
            del result_dict[app_user]
            continue
        saved_points = result_dict[app_user]
        saved_points.user_details = ExtendedUserDetailsTO.fromUserProfile(profile_info, None)
        app_info = get_app_info_cached(saved_points.user_details.app_id)
        saved_points.user_details.app_name = app_info.name
        saved_points.visits = sorted(saved_points.visits,
                                     key=lambda x:-x.timestamp)

    r = BaseLoyaltyCustomersTO()
    r.loyalty_type = SolutionLoyaltySettings.LOYALTY_TYPE_LOTTERY
    r.cursor = cursor_.decode("utf8")
    r.has_more = has_more
    r.customers = sorted(result_dict.itervalues(),
                    key=lambda x:-x.visits[0].timestamp)
    return r

@rest("/common/city_wide_lottery/customer_points/detail", "get", read_only_access=True)
@returns(LoyaltyCustomerPointsTO)
@arguments(city_app_id=unicode, email=unicode, app_id=unicode)
def load_city_wide_lottery_detail_customer_points(city_app_id, email, app_id):
    app_user = create_app_user_by_email(email, app_id)
    visits = get_solution_city_wide_lottery_loyalty_visits_for_user(city_app_id, app_user)
    r = LoyaltyCustomerPointsTO()

    # XXX: don't use get_profile_infos
    profile_infos = get_profile_infos([app_user], allow_none_in_results=True)
    for app_user, profile_info in zip([app_user], profile_infos):
        if not profile_info or profile_info.isServiceIdentity:
            continue
        r.user_details = ExtendedUserDetailsTO.fromUserProfile(profile_info, None)
        app_info = get_app_info_cached(r.user_details.app_id)
        r.user_details.app_name = app_info.name
    r.visits = [SolutionLoyaltyVisitTO.fromModel(visit) for visit in visits]
    return r

@rest("/common/city_wide_lottery/chance", "get", read_only_access=True)
@returns(LoyaltyLotteryChanceTO)
@arguments(city_app_id=unicode, email=unicode, app_id=unicode)
def load_city_wide_lottery_chance_user(city_app_id, email, app_id):
    app_user = create_app_user_by_email(email, app_id)
    r = LoyaltyLotteryChanceTO()
    r.total_visits, r.my_visits, r.chance = calculate_city_wide_lottery_chance_for_user(city_app_id, app_user)
    return r


@rest("/common/city_wide_lottery/add", "post")
@returns(ReturnStatusTO)
@arguments(city_app_id=unicode, winnings=unicode, date=TimestampTO, x_winners=(int, long))
def add_city_wide_lottery_info(city_app_id, winnings, date, x_winners):
    service_user = users.get_current_user()
    sln_settings = get_solution_settings(service_user)
    try:
        now_ = now()
        end_timestamp = date.toEpoch()
        if end_timestamp <= (now_ + 24 * 3600):
            raise BusinessException("end-date-24h-in-future")

        ll_info = SolutionCityWideLottery.load_pending(city_app_id)
        if ll_info:
            logging.warn("end_timestamp: %s", end_timestamp)
            logging.warn("ll_info.end_timestamp: %s", ll_info.end_timestamp)
            if end_timestamp <= ll_info.end_timestamp:
                raise BusinessException("lottery-time-bigger-first-upcoming")

        ll_info = SolutionCityWideLottery(parent=SolutionCityWideLottery.create_parent_key(city_app_id))
        ll_info.timestamp = now_
        ll_info.end_timestamp = end_timestamp
        ll_info.schedule_loot_time = ll_info.end_timestamp - 24 * 3600
        ll_info.winnings = winnings
        ll_info.x_winners = x_winners
        ll_info.winners = []
        ll_info.winner_info = []
        ll_info.skip_winners = []
        ll_info.deleted = False
        ll_info.pending = True
        ll_info.put()

        send_message(service_user, u"solutions.common.loyalty.lottery.update")

        return RETURNSTATUS_TO_SUCCESS
    except BusinessException, e:
        return ReturnStatusTO.create(False, common_translate(sln_settings.main_language, SOLUTION_COMMON, e.message))


@rest("/common/city_wide_lottery/edit", "post")
@returns(ReturnStatusTO)
@arguments(key=unicode, winnings=unicode, date=TimestampTO, x_winners=(int, long))
def edit_city_wide_lottery_info(key, winnings, date, x_winners):
    ll_info_edit = SolutionCityWideLottery.get(key)
    if not ll_info_edit:
        return RETURNSTATUS_TO_SUCCESS

    service_user = users.get_current_user()
    sln_settings = get_solution_settings(service_user)

    try:
        now_ = now()
        end_timestamp = date.toEpoch()
        if end_timestamp <= (now_ + 24 * 3600):
            raise BusinessException("end-date-24h-in-future")

        ll_info = SolutionCityWideLottery.load_pending(ll_info_edit.app_id)
        if ll_info_edit.key() != ll_info.key() and end_timestamp <= ll_info.end_timestamp:
            raise BusinessException("lottery-time-bigger-first-upcoming")

        ll_info_edit.end_timestamp = end_timestamp
        ll_info_edit.schedule_loot_time = ll_info_edit.end_timestamp - 24 * 3600
        ll_info_edit.winnings = winnings
        ll_info_edit.x_winners = x_winners
        ll_info_edit.put()

        send_message(service_user, u"solutions.common.loyalty.lottery.update")

        return RETURNSTATUS_TO_SUCCESS
    except BusinessException, e:
        return ReturnStatusTO.create(False, common_translate(sln_settings.main_language, SOLUTION_COMMON, e.message))


@rest("/common/city_wide_lottery/delete", "post")
@returns(ReturnStatusTO)
@arguments(key=unicode)
def delete_city_wide_lottery_info(key):
    ll_info_delete = SolutionCityWideLottery.get(key)
    if not ll_info_delete:
        return RETURNSTATUS_TO_SUCCESS

    service_user = users.get_current_user()
    sln_settings = get_solution_settings(service_user)

    try:
        ll_info = SolutionCityWideLottery.load_pending(ll_info_delete.app_id)
        if ll_info_delete.key() == ll_info.key():
            raise RETURNSTATUS_TO_SUCCESS
        if ll_info_delete.schedule_loot_time > 0:
            ll_info_delete.delete()

        send_message(service_user, u"solutions.common.loyalty.lottery.update")

        return RETURNSTATUS_TO_SUCCESS
    except BusinessException, e:
        return ReturnStatusTO.create(False, common_translate(sln_settings.main_language, SOLUTION_COMMON, e.message))


@rest("/common/city_wide_lottery/close", "post")
@returns(ReturnStatusTO)
@arguments(key=unicode)
def close_city_wide_lottery_info(key):
    service_user = users.get_current_user()
    try:
        ll_info = SolutionCityWideLottery.get(key)
        if ll_info and not ll_info.pending and not ll_info.deleted:
            ll_info.deleted = True
            ll_info.put()

        send_message(service_user, u"solutions.common.loyalty.lottery.update", service_identity=ll_info.service_identity)

        return RETURNSTATUS_TO_SUCCESS
    except BusinessException, e:
        sln_settings = get_solution_settings(service_user)
        return ReturnStatusTO.create(False, common_translate(sln_settings.main_language, SOLUTION_COMMON, e.message))


@rest("/common/city_wide_lottery/load", "get", read_only_access=True)
@returns([CityWideLotteryInfoTO])
@arguments(city_app_id=unicode)
def load_city_wide_lottery_info(city_app_id):
    return [CityWideLotteryInfoTO.fromModel(ll_info) for ll_info in SolutionCityWideLottery.load_all(city_app_id)]
