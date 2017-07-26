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
# @@license_version:1.2@@

import datetime
import logging
import urllib

from mcfw.consts import MISSING
from mcfw.properties import unicode_property, long_property, bool_property, typed_property, long_list_property, \
    unicode_list_property
from mcfw.rpc import parse_complex_value, serialize_complex_value
from rogerthat.dal.profile import get_user_profile
from rogerthat.settings import get_server_settings
from rogerthat.to import ReturnStatusTO
from rogerthat.to.messaging import AttachmentTO
from rogerthat.utils import get_epoch_from_datetime, urlencode
from rogerthat.utils.app import get_human_user_from_app_user
from solutions import translate as common_translate
from solutions.common import SOLUTION_COMMON
from solutions.common.models import SolutionInboxMessage, SolutionBrandingSettings
from solutions.common.models.agenda import Event, SolutionCalendarAdmin
from solutions.common.models.properties import MenuCategory


class SolutionUserKeyLabelTO(object):
    key = unicode_property('1')
    label = unicode_property('2')


class SolutionInboxForwarder(SolutionUserKeyLabelTO):
    type = unicode_property('51')


class SolutionInboxMessageTO(object):
    key = unicode_property('1')
    category = unicode_property('2')  # only filled in on parent message
    timestamp = long_property('3')
    message = unicode_property('4')

    reply_enabled = bool_property('5')
    starred = bool_property('6')  # only filled in on parent message
    read = bool_property('7')  # only filled in on parent message
    trashed = bool_property('8')  # only filled in on parent message
    inbox = unicode_property('9')

    sent_by_service = bool_property('10')
    sender_name = unicode_property('11')
    sender_avatar_url = unicode_property('12')
    sender_language = unicode_property('13')
    sender_email = unicode_property('14')

    icon = unicode_property('15')
    icon_color = unicode_property('16')
    size = long_property('17')

    picture_urls = unicode_list_property('18')
    video_urls = unicode_list_property('19')
    chat_topic = unicode_property('20')

    @staticmethod
    def fromModel(message, sln_settings, sln_i_settings, show_last=False):
        to = SolutionInboxMessageTO()
        to.key = unicode(message.solution_inbox_message_key)
        to.category = unicode(message.category) if message.category else None
        if show_last and message.last_timestamp:
            to.timestamp = message.last_timestamp
        else:
            to.timestamp = message.timestamp
        if show_last and message.last_message:
            to.message = message.last_message
        else:
            to.message = message.message

        if show_last and len(to.message) > 250:
            to.message = u"%s..." % to.message[:200]

        to.reply_enabled = message.reply_enabled
        to.starred = message.starred
        to.read = message.read
        to.trashed = message.trashed
        if message.deleted:
            to.inbox = SolutionInboxMessage.INBOX_NAME_DELETED
        elif message.trashed:
            to.inbox = SolutionInboxMessage.INBOX_NAME_TRASH
        elif message.starred:
            to.inbox = SolutionInboxMessage.INBOX_NAME_STARRED
        elif not message.read:
            to.inbox = SolutionInboxMessage.INBOX_NAME_UNREAD
        else:
            to.inbox = SolutionInboxMessage.INBOX_NAME_READ

        to.sent_by_service = message.sent_by_service
        if message.sender:
            to.sender_name = message.sender.name
            to.sender_avatar_url = message.sender.avatar_url
            to.sender_language = message.sender.language
            to.sender_email = message.sender.email
        else:
            to.sender_name = sln_i_settings.name
            to.sender_avatar_url = None
            to.sender_language = sln_settings.main_language
            to.sender_email = sln_i_settings.qualified_identifier

        to.icon = message.icon
        to.icon_color = message.icon_color(sln_settings.solution)
        to.size = 1 + (len(message.child_messages) if message.child_messages else 0)

        to.picture_urls = message.picture_urls
        to.video_urls = message.video_urls
        to.chat_topic = common_translate(sln_settings.main_language, SOLUTION_COMMON,
                                         message.chat_topic_key) if message.chat_topic_key else ""
        return to


class SolutionInboxesTO(object):
    name = unicode_property('1')
    cursor = unicode_property('2')
    has_more = bool_property('3')
    messages = typed_property('4', SolutionInboxMessageTO, True)

    @staticmethod
    def fromModel(name, cursor, messages, has_more, sln_settings, sln_i_settings, show_last=False):
        to = SolutionInboxesTO()
        to.name = name
        to.cursor = cursor
        to.has_more = has_more
        to.messages = [SolutionInboxMessageTO.fromModel(message, sln_settings, sln_i_settings, show_last) for message in messages]
        return to


class SolutionSettingsTO(object):
    name = unicode_property('1')
    description = unicode_property('2')
    opening_hours = unicode_property('3')
    address = unicode_property('4')
    phone_number = unicode_property('5')
    updates_pending = bool_property('6')
    facebook_page = unicode_property('7')
    facebook_name = unicode_property('8')
    facebook_action = unicode_property('9')
    currency = unicode_property('10')
    search_enabled = bool_property('11')
    timezone = unicode_property('12')
    events_visible = bool_property('13')
    event_notifications_enabled = bool_property('14')
    search_keywords = unicode_property('15')
    email_address = unicode_property('16')
    inbox_email_reminders = bool_property('17')
    twitter_username = unicode_property('18')
    holidays = long_list_property('19')
    holiday_out_of_office_message = unicode_property('20')
    iban = unicode_property('21')
    bic = unicode_property('22')
    publish_changes_users = unicode_list_property('23', default=[])

    @staticmethod
    def fromModel(sln_settings, sln_i_settings):
        to = SolutionSettingsTO()
        to.name = sln_i_settings.name
        to.description = sln_i_settings.description
        to.opening_hours = sln_i_settings.opening_hours
        to.address = sln_i_settings.address
        to.phone_number = sln_i_settings.phone_number
        to.currency = sln_settings.currency
        to.updates_pending = sln_settings.updates_pending
        to.facebook_page = sln_settings.facebook_page
        to.facebook_name = sln_settings.facebook_name
        to.facebook_action = sln_settings.facebook_action
        to.search_enabled = sln_settings.search_enabled
        to.timezone = sln_settings.timezone
        to.events_visible = sln_settings.events_visible
        to.event_notifications_enabled = sln_settings.event_notifications_enabled
        to.search_keywords = sln_i_settings.search_keywords
        to.email_address = sln_i_settings.qualified_identifier or sln_settings.service_user.email()
        to.inbox_email_reminders = sln_i_settings.inbox_email_reminders_enabled if sln_i_settings.inbox_email_reminders_enabled else False
        to.twitter_username = sln_settings.twitter_username
        to.holidays = sln_i_settings.holidays
        to.holiday_out_of_office_message = sln_i_settings.holiday_out_of_office_message
        to.iban = sln_settings.iban
        to.bic = sln_settings.bic
        to.publish_changes_users = sln_settings.publish_changes_users
        return to


class ProvisionResponseTO(object):
    login = unicode_property('1')
    password = unicode_property('2')
    auto_login_url = unicode_property('3')


class ProvisionReturnStatusTO(ReturnStatusTO):
    service = typed_property('51', ProvisionResponseTO)

    @classmethod
    def create(cls, success=True, errormsg=None, service=None):
        r = super(ProvisionReturnStatusTO, cls).create(success=success, errormsg=errormsg)
        r.service = service
        return r


class UrlReturnStatusTO(ReturnStatusTO):
    url = unicode_property('51')

    @classmethod
    def create(cls, success=True, errormsg=None, url=None):
        r = super(UrlReturnStatusTO, cls).create(success=success, errormsg=errormsg)
        r.url = url
        return r


class MenuTO(object):
    categories = typed_property('1', MenuCategory, True)
    predescription = unicode_property('2')
    postdescription = unicode_property('3')
    name = unicode_property('4')

    @staticmethod
    def fromMenuObject(obj):
        menu = MenuTO()
        menu.name = obj.name
        menu.predescription = obj.predescription
        menu.postdescription = obj.postdescription
        menu.categories = list()
        for category_obj in sorted(obj.categories, key=lambda x: x.index):
            # copy
            menu.categories.append(parse_complex_value(MenuCategory,
                                                       serialize_complex_value(category_obj, MenuCategory, False),
                                                       False))
        return menu


class TimestampTO(object):
    year = long_property('1')
    month = long_property('2')  # 1=January, ..., 12=December
    day = long_property('3')
    hour = long_property('4')
    minute = long_property('5')

    @staticmethod
    def fromDatetime(obj):
        t = TimestampTO()
        t.year = obj.year
        t.month = obj.month
        t.day = obj.day
        t.hour = obj.hour
        t.minute = obj.minute
        return t

    @staticmethod
    def fromEpoch(obj):
        return TimestampTO.fromDatetime(datetime.datetime.utcfromtimestamp(obj))

    def toDateTime(self):
        return datetime.datetime(self.year, self.month, self.day, self.hour, self.minute)

    def toEpoch(self):
        return get_epoch_from_datetime(self.toDateTime())


class EventGuestTO(object):
    email = unicode_property('1')
    name = unicode_property('2')
    language = unicode_property('3')
    avatar_url = unicode_property('4')
    app_id = unicode_property('5')
    status = long_property('6')

    @staticmethod
    def fromEventGuest(obj):
        e = EventGuestTO()
        e.email = obj.guest.email
        e.name = obj.guest.name
        e.language = obj.guest.language
        e.avatar_url = obj.guest.avatar_url
        e.app_id = obj.guest.app_id
        e.status = obj.status
        return e


class PublicEventItemTO(object):
    id = long_property('1')
    title = unicode_property('2')
    place = unicode_property('3')
    description = unicode_property('4')
    start_dates = long_list_property('5')
    end_dates = long_list_property('6')

    @staticmethod
    def fromPublicEventItemObject(obj):
        item = PublicEventItemTO()
        item.id = obj.key().id()
        item.title = unicode(obj.title)
        item.place = unicode(obj.place)
        item.description = unicode(obj.description)
        item.start_dates = list()
        item.end_dates = list()
        for start_date, end_date in zip(obj.start_dates, obj.end_dates):
            item.start_dates.append(start_date)
            sd = datetime.datetime.utcfromtimestamp(start_date)
            seconds_since_midnight = (sd - sd.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
            if end_date >= seconds_since_midnight:
                item.end_dates.append(start_date - seconds_since_midnight + end_date)
            else:
                item.end_dates.append(start_date - seconds_since_midnight + 86400 + end_date)
        return item


class EventItemTO(object):
    id = long_property('1')
    title = unicode_property('2')
    place = unicode_property('3')
    description = unicode_property('4')
    start_dates = typed_property('5', TimestampTO, True)
    end_dates = long_list_property('6')
    can_edit = bool_property('7')
    source = long_property('8')
    external_link = unicode_property('9')
    picture = unicode_property('10')
    new_picture = bool_property('11')
    end_dates_timestamps = typed_property('12', TimestampTO, True)
    calendar_id = long_property('13')
    organizer = unicode_property('14')

    @staticmethod
    def fromEventItemObject(obj, include_picture=False, destination_app=True):
        item = EventItemTO()
        item.id = obj.key().id()
        item.title = unicode(obj.title)
        item.place = unicode(obj.place)
        item.description = unicode(obj.description)
        item.start_dates = list()
        item.end_dates = list()
        item.end_dates_timestamps = list()
        for start_date, end_date in zip(obj.start_dates, obj.end_dates):
            item.start_dates.append(TimestampTO.fromDatetime(datetime.datetime.utcfromtimestamp(start_date)))
            item.end_dates.append(end_date)
            sd = datetime.datetime.utcfromtimestamp(start_date)
            seconds_since_midnight = (sd - sd.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
            offset = 0 if end_date >= seconds_since_midnight else 86400
            item.end_dates_timestamps.append(TimestampTO.fromDatetime(
                    datetime.datetime.utcfromtimestamp(start_date - seconds_since_midnight + offset + end_date)))

        item.can_edit = obj.source == Event.SOURCE_CMS
        item.source = obj.source
        if obj.source == Event.SOURCE_UITDATABANK_BE:
            item.external_link = u"http://www.uitinvlaanderen.be/agenda/e/%s/%s" % (urlencode({"": obj.title})[1:],
                                                                                    urlencode({"": obj.external_id})[
                                                                                    1:])
        elif obj.source == Event.SOURCE_GOOGLE_CALENDAR and not destination_app:
            item.external_link = obj.external_link
        elif obj.source == Event.SOURCE_SCRAPER:
            item.external_link = obj.external_link
        else:
            item.external_link = obj.url or None
        if include_picture:
            item.picture = unicode(obj.picture) if obj.picture else None
        else:
            if obj.picture:
                server_settings = get_server_settings()
                base_url = server_settings.baseUrl
                params = urllib.urlencode(dict(service_user_email=obj.service_user.email(),
                                               event_id=item.id,
                                               picture_version=obj.picture_version))
                item.picture = "%s/solutions/common/public/events/picture?%s" % (base_url, params)
            else:
                item.picture = None
        item.new_picture = False

        item.calendar_id = obj.calendar_id
        item.organizer = obj.organizer
        return item

class SolutionCalendarTO(object):
    id = long_property('1')
    name = unicode_property('2')
    admins = typed_property('3', SolutionUserKeyLabelTO, True)
    can_delete = bool_property('4')
    connector_qrcode = unicode_property('5')
    events = typed_property('6', EventItemTO, True)
    broadcast_enabled = bool_property('7')

    @staticmethod
    def fromSolutionCalendar(sln_settings, obj, include_events=False, include_events_picture=False):
        item = SolutionCalendarTO()
        item.id = obj.calendar_id
        item.name = obj.name
        item.admins = list()
        for admin in obj.get_admins():
            sif = SolutionUserKeyLabelTO()
            sif.key = admin.app_user.email()
            human_user = get_human_user_from_app_user(admin.app_user)
            up = get_user_profile(admin.app_user)
            sif.label = u"%s (%s)" % (up.name, human_user.email())
            item.admins.append(sif)
        item.can_delete = sln_settings.default_calendar != item.id
        item.connector_qrcode = obj.connector_qrcode
        item.events = list()
        if include_events:
            for e in obj.events:
                item.events.append(EventItemTO.fromEventItemObject(e, include_events_picture))
        item.broadcast_enabled = obj.broadcast_enabled
        return item

class SolutionCalendarWebTO(SolutionCalendarTO):
    cursor = unicode_property('50')
    has_more = bool_property('51')

    @staticmethod
    def fromSolutionCalendar(sln_settings, obj, include_events=False, include_events_picture=False,
                             include_admin_deleting=True, cursor=None, cursor_count=10):
        item = SolutionCalendarWebTO()
        item.id = obj.calendar_id
        item.name = obj.name
        item.admins = list()
        for admin in obj.get_admins():
            up = get_user_profile(admin.app_user)
            if up:
                sif = SolutionUserKeyLabelTO()
                sif.key = admin.app_user.email()
                human_user = get_human_user_from_app_user(admin.app_user)
                sif.label = u"%s (%s)" % (up.name, human_user.email())
                item.admins.append(sif)
        item.can_delete = sln_settings.default_calendar != item.id
        item.connector_qrcode = obj.connector_qrcode
        item.events = list()
        item.cursor = None
        item.has_more = False
        if include_events:
            item.cursor, events, item.has_more = obj.events_with_cursor(cursor, cursor_count)
            for e in events:
                item.events.append(EventItemTO.fromEventItemObject(e, include_events_picture, False))
        item.broadcast_enabled = obj.broadcast_enabled
        return item

class SolutionGoogleCalendarTO(object):
    key = unicode_property('1')
    label = unicode_property('2')
    enabled = bool_property('3')

class SolutionGoogleCalendarStatusTO(object):
    enabled = bool_property('1')
    calendars = typed_property('3', SolutionGoogleCalendarTO, True)

class SolutionAppointmentWeekdayTimeframeTO(object):
    id = long_property('1')
    day = long_property('2')
    time_from = long_property('3')
    time_until = long_property('4')
    day_str = unicode_property('5')

    @classmethod
    def fromModel(cls, obj, language):
        s = cls()
        s.id = obj.id
        s.day = obj.day
        s.time_from = obj.time_from
        s.time_until = obj.time_until
        s.day_str = obj.day_str(language)
        return s


class SolutionOrderWeekdayTimeframeTO(SolutionAppointmentWeekdayTimeframeTO):
    pass


class SolutionAppointmentSettingsTO(object):
    text_1 = unicode_property('1')

    @staticmethod
    def fromModel(obj, language):
        to = SolutionAppointmentSettingsTO()
        text_1 = None
        if obj:
            text_1 = obj.text_1

        if not text_1:
            text_1 = common_translate(language, SOLUTION_COMMON, 'appointment-1')

        to.text_1 = text_1
        return to


class SolutionStaticContentPositionTO(object):
    x = long_property('1')
    y = long_property('2')
    z = long_property('3')

    @staticmethod
    def fromModel(obj):
        pos = SolutionStaticContentPositionTO()
        pos.x = obj.coords[0]
        pos.y = obj.coords[1]
        pos.z = obj.coords[2]
        return pos


class SolutionStaticContentTO(object):
    sc_type = long_property('1')
    position = typed_property('2', SolutionStaticContentPositionTO, False)
    icon_label = unicode_property('3')
    icon_name = unicode_property('4')
    text_color = unicode_property('5')
    background_color = unicode_property('6')
    html_content = unicode_property('7')
    visible = bool_property('8')
    id = long_property('9')
    website = unicode_property('10')


    @property
    def position_str(self):
        return u"%sx%sx%s" % (self.position.z, self.position.x, self.position.y)

    @staticmethod
    def fromModel(obj):
        sc = SolutionStaticContentTO()
        sc.sc_type = 1 if obj.sc_type is None else obj.sc_type
        sc.position = SolutionStaticContentPositionTO.fromModel(obj)
        sc.old_position = None
        sc.icon_label = obj.icon_label
        sc.icon_name = obj.icon_name
        sc.text_color = obj.text_color
        sc.background_color = obj.background_color
        sc.html_content = obj.html_content
        sc.visible = obj.visible
        sc.website = obj.website
        sc.id = obj.key().id()
        return sc


class ServiceMenuFreeSpotTO(object):
    x = long_property('1')
    y = long_property('2')
    z = long_property('3')

    @staticmethod
    def fromList(obj):
        spot = ServiceMenuFreeSpotTO()
        spot.x = obj[0]
        spot.y = obj[1]
        spot.z = obj[2]
        return spot


class ServiceMenuFreeSpotsTO(object):
    spots = typed_property('1', ServiceMenuFreeSpotTO, True)

    @staticmethod
    def fromList(obj):
        spots = ServiceMenuFreeSpotsTO()
        spots.spots = list()
        for o in obj:
            spots.spots.append(ServiceMenuFreeSpotTO.fromList(o))
        return spots


class BrandingSettingsTO(object):
    color_scheme = unicode_property('1')
    background_color = unicode_property('2')
    text_color = unicode_property('3')
    menu_item_color = unicode_property('4')
    show_identity_name = bool_property('5')
    show_avatar = bool_property('6')

    @classmethod
    def from_model(cls, model):
        """
        Args:
            model (solutions.common.models.SolutionBrandingSettings)
        """
        to = cls()
        to.color_scheme = model.color_scheme
        to.background_color = model.background_color or SolutionBrandingSettings.default_background_color(to.color_scheme)
        to.text_color = model.text_color or SolutionBrandingSettings.default_text_color(to.color_scheme)
        to.menu_item_color = model.menu_item_color or SolutionBrandingSettings.default_menu_item_color(to.color_scheme)
        to.show_identity_name = model.show_identity_name
        to.show_avatar = model.show_avatar
        return to


class SolutionRepairSettingsTO(object):
    text_1 = unicode_property('1')

    @staticmethod
    def fromModel(obj, language):
        to = SolutionRepairSettingsTO()
        text_1 = None
        if obj:
            text_1 = obj.text_1

        if not text_1:
            text_1 = common_translate(language, SOLUTION_COMMON, 'repair-1')

        to.text_1 = text_1
        return to


class SolutionRepairOrderTO(object):
    key = unicode_property('1')
    description = unicode_property('2')
    status = long_property('3')
    sender_name = unicode_property('4')
    sender_avatar_url = unicode_property('5')
    timestamp = long_property('6')
    picture_url = unicode_property('7')
    solution_inbox_message_key = unicode_property('8')

    @staticmethod
    def fromModel(model):
        to = SolutionRepairOrderTO()
        to.key = unicode(model.solution_repair_order_key)
        to.description = model.description
        to.status = model.status
        to.sender_name = model.sender.name
        to.sender_avatar_url = model.sender.avatar_url
        to.timestamp = model.timestamp
        to.picture_url = model.picture_url
        to.solution_inbox_message_key = model.solution_inbox_message_key
        return to


class SandwichSettingTO(object):
    id = long_property('1')
    description = unicode_property('2')
    price = long_property('3')
    order = long_property('4')
    deleted = bool_property('5')
    price_in_euro = unicode_property('6')

    @staticmethod
    def fromModel(model):
        ss = SandwichSettingTO()
        ss.id = model.id
        ss.description = model.description
        ss.price = model.price
        ss.order = model.order
        ss.deleted = False
        ss.price_in_euro = model.price_in_euro
        return ss


class SandwichSettingsTO(object):
    show_prices = bool_property('1')
    types = typed_property('2', SandwichSettingTO, True)
    toppings = typed_property('3', SandwichSettingTO, True)
    options = typed_property('4', SandwichSettingTO, True)
    currency = unicode_property('5')
    days = long_property('6')
    from_ = long_property('7')
    till = long_property('8')
    reminder_days = long_property('9')
    reminder_message = unicode_property('10')
    reminder_at = long_property('11')
    leap_time_enabled = bool_property('12')
    leap_time = long_property('13')
    leap_time_type = long_property('14')

    @classmethod
    def from_model(cls, sandwich_settings, types, toppings, options, currency):
        """
        Args:
            sandwich_settings (solutions.common.models.sandwich.SandwichSettings):
            types (list of solutions.common.models.sandwich.SandwichType)
            toppings (list of solutions.common.models.sandwich.SandwichTopping)
            options (list of solutions.common.models.sandwich.SandwichOption)
            currency (unicode)
        """
        to = cls()
        to.show_prices = sandwich_settings.show_prices
        to.types = [SandwichSettingTO.fromModel(t) for t in types]
        to.toppings = [SandwichSettingTO.fromModel(t) for t in toppings]
        to.options = [SandwichSettingTO.fromModel(t) for t in options]
        to.currency = currency
        to.days = sandwich_settings.status_days
        to.from_ = sandwich_settings.time_from
        to.till = sandwich_settings.time_until
        to.reminder_days = sandwich_settings.broadcast_days
        to.reminder_message = sandwich_settings.reminder_broadcast_message
        to.reminder_at = sandwich_settings.remind_at
        to.leap_time_enabled = sandwich_settings.leap_time_enabled
        to.leap_time = sandwich_settings.leap_time
        to.leap_time_type = sandwich_settings.leap_time_type
        return to


class SandwichOrderTO(object):
    id = unicode_property('1')
    timestamp = long_property('2')
    type = typed_property('3', SandwichSettingTO, False)
    topping = typed_property('4', SandwichSettingTO, False)
    options = typed_property('5', SandwichSettingTO, True)
    price = long_property('6')
    price_in_euro = unicode_property('7')
    remark = unicode_property('8')
    sender_name = unicode_property('9')
    sender_avatar_url = unicode_property('10')
    status = long_property('11')
    solution_inbox_message_key = unicode_property('12')
    takeaway_time = long_property('13')

    @staticmethod
    def fromModel(model):
        to = SandwichOrderTO()
        to.id = model.id
        to.timestamp = model.order_time
        to.type = SandwichSettingTO.fromModel(model.sandwich_type)
        topping = model.sandwich_topping
        to.topping = SandwichSettingTO.fromModel(topping) if topping else None
        to.options = list()
        for option in model.sandwich_options:
            to.options.append(SandwichSettingTO.fromModel(option))
        to.price = model.price
        to.price_in_euro = model.price_in_euro
        to.remark = model.remark
        to.sender_name = model.sender.name
        to.sender_avatar_url = model.sender.avatar_url
        to.status = model.status
        to.solution_inbox_message_key = model.solution_inbox_message_key
        to.takeaway_time = model.takeaway_time
        return to


class SolutionGroupPurchaseSubscriptionTO(object):
    id = long_property('1')
    timestamp = long_property('2')
    units = long_property('3')
    sender_name = unicode_property('4')
    sender_avatar_url = unicode_property('5')


class SolutionGroupPurchaseTO(object):
    id = long_property('1')
    title = unicode_property('2')
    description = unicode_property('3')
    picture = unicode_property('4')
    units = long_property('5')
    unit_description = unicode_property('6')
    unit_price = long_property('7')  # in euro cents
    unit_price_in_euro = unicode_property('8')
    min_units_pp = long_property('9')
    max_units_pp = long_property('10')
    time_from = long_property('11')  # epoch
    time_until = long_property('12')  # epoch
    units_available = long_property('13')
    subscriptions = typed_property('14', SolutionGroupPurchaseSubscriptionTO, True)
    new_picture = bool_property('15')

    @staticmethod
    def fromModel(model, include_picture=False, incude_subscriptions=False):

        to = SolutionGroupPurchaseTO()
        to.id = model.id
        to.title = model.title
        to.description = model.description

        if include_picture:
            to.picture = unicode(model.picture) if model.picture else None
        else:
            if model.picture:
                server_settings = get_server_settings()
                base_url = server_settings.baseUrl
                params = urllib.urlencode(dict(service_user_email=model.service_user.email(),
                                               service_identity=model.service_identity,
                                               group_purchase_id=to.id,
                                               picture_version=model.picture_version))
                to.picture = "%s/solutions/common/public/group_purchase/picture?%s" % (base_url, params)
            else:
                to.picture = None

        to.units = model.units
        to.unit_description = model.unit_description
        to.unit_price = model.unit_price
        to.unit_price_in_euro = model.unit_price_in_euro
        to.min_units_pp = model.min_units_pp
        to.max_units_pp = model.max_units_pp
        to.time_from = model.time_from
        to.time_until = model.time_until
        to.units_available = model.units
        to.subscriptions = list()
        for sgpe in model.subscriptions:
            to.units_available -= sgpe.units
            if incude_subscriptions:
                toe = SolutionGroupPurchaseSubscriptionTO()
                toe.id = sgpe.id
                toe.timestamp = sgpe.timestamp
                toe.units = sgpe.units
                toe.sender_name = sgpe.sender.name if sgpe.sender else sgpe.name
                toe.sender_avatar_url = sgpe.sender.avatar_url if sgpe.sender else None
                to.subscriptions.append(toe)
        to.new_picture = False
        return to


class SolutionGroupPurchaseSettingsTO(object):
    visible = bool_property('1')

    @staticmethod
    def fromModel(model):
        to = SolutionGroupPurchaseSettingsTO()
        to.visible = model.visible
        return to


class CreditCardTO(object):
    brand = unicode_property('1')
    exp_month = long_property('2')
    exp_year = long_property('3')
    last4 = unicode_property('4')


class UrlTO(object):
    url = unicode_property('1')
    name = unicode_property('2')


class SolutionScheduledBroadcastTO(object):
    key = unicode_property('1')
    scheduled = typed_property('2', TimestampTO, False)
    broadcast_type = unicode_property('3')
    message = unicode_property('4')
    target_audience_enabled = bool_property('5')
    target_audience_min_age = long_property('6')
    target_audience_max_age = long_property('7')
    target_audience_gender = unicode_property('8')
    attachments = typed_property('9', AttachmentTO, True)
    urls = typed_property('10', UrlTO, True)

    @staticmethod
    def fromModel(model):
        ssb = SolutionScheduledBroadcastTO()
        ssb.key = unicode(model.key_str)
        ssb.scheduled = TimestampTO.fromEpoch(model.broadcast_epoch)
        ssb.broadcast_type = model.broadcast_type
        ssb.message = model.message
        ssb.target_audience_enabled = model.target_audience_enabled
        ssb.target_audience_min_age = model.target_audience_min_age
        ssb.target_audience_max_age = model.target_audience_max_age
        ssb.target_audience_gender = model.target_audience_gender
        ssb.attachments = model.attachments
        ssb.urls = model.urls or list()
        return ssb


class SolutionEmailSettingsTO(object):
    inbox = bool_property('1')

    @staticmethod
    def fromModel(sln_email_settings, service_user):
        to = SolutionEmailSettingsTO()
        to.inbox = service_user in sln_email_settings.visible_in_inbox
        return to


class ServiceTO(object):
    customer_id = long_property('1')
    name = unicode_property('2')
    address1 = unicode_property('3')
    address2 = unicode_property('4')
    zip = unicode_property('5')
    city = unicode_property('6')
    user_email = unicode_property('7')
    telephone = unicode_property('8')
    language = unicode_property('9')
    modules = unicode_list_property('10')
    broadcast_types = unicode_list_property('11')
    organization_type = long_property('12')
    vat = unicode_property('13')
    website = unicode_property('14')
    facebook_page = unicode_property('15')

    def __init__(self, customer_id=None, name=None, address1=None, address2=None, zip_code=None, city=None,
                 user_email=None, telephone=None, language=None, modules=None, broadcast_types=None,
                 organization_type=None, vat=None, website=None, facebook_page=None):
        self.customer_id = customer_id
        self.name = name
        self.address1 = address1
        self.address2 = address2
        self.zip = zip_code
        self.city = city
        self.user_email = user_email
        self.telephone = telephone
        self.language = language
        self.modules = modules
        self.broadcast_types = broadcast_types
        self.organization_type = organization_type
        self.vat = vat
        self.website = website
        self.facebook_page = facebook_page


class ImageReturnStatusTO(ReturnStatusTO):
    image_id = long_property('51')

    @classmethod
    def create(cls, success=True, errormsg=None, image_id=None):
        r = super(ImageReturnStatusTO, cls).create(success=success, errormsg=errormsg)
        r.image_id = image_id
        return r


class PictureReturnStatusTO(ReturnStatusTO):
    picture = unicode_property('51')

    @classmethod
    def create(cls, success=True, errormsg=None, picture=None):
        r = super(PictureReturnStatusTO, cls).create(success=success, errormsg=errormsg)
        r.picture = picture
        return r


class BroadcastTypesTO(object):
    all = unicode_list_property('1')
    editable = unicode_list_property('2')

    @classmethod
    def create(cls, all_, editable):
        to = cls()
        to.all = all_
        to.editable = editable
        return to


class ServiceMenuItemWithCoordinatesTO(object):
    label = unicode_property('1')
    iconUrl = unicode_property('2')
    coords = unicode_property('3')
    iconName = unicode_property('4')

    @classmethod
    def create(cls, label, iconName, iconUrl, coords):
        to = cls()
        to.label = label
        to.iconName = iconName
        to.iconUrl = iconUrl
        to.coords = unicode(coords)
        return to


class ServiceMenuItemWithCoordinatesListTO(object):
    menu_items = typed_property('3', ServiceMenuItemWithCoordinatesTO, True)

    @classmethod
    def create(cls, menu_items):
        to = cls()
        to.menu_items = menu_items
        return to


class BrandingSettingsAndMenuItemsTO(object):
    branding_settings = typed_property('4', BrandingSettingsTO, False)
    menu_item_rows = typed_property('5', ServiceMenuItemWithCoordinatesListTO, True)

    @classmethod
    def create(cls, branding_settings, menu_item_rows):
        to = cls()
        to.branding_settings = branding_settings
        to.menu_item_rows = menu_item_rows
        return to

class SaveSettingsResultTO(object):
    address_geocoded = bool_property('1')

class SaveSettingsReturnStatusTO(ReturnStatusTO):
    result = typed_property('51', SaveSettingsResultTO)

    @classmethod
    def create(cls, success=True, errormsg=None, result=None):
        r = super(SaveSettingsReturnStatusTO, cls).create(success=success, errormsg=errormsg)
        r.result = result
        return r


class AppUserRolesTO(object):
    app_user_email = unicode_property('1')
    app_id = unicode_property('2')

    inbox_forwarder = bool_property('3')
    calendar_admin = bool_property('4')
    news_publisher = bool_property('5')

    # forwarder types assigned to app user (mobile, email)
    forwarder_types = unicode_list_property('6')

    # in case the user is a calendar admin
    # he may be an admin of many calendars (list)
    calendars = typed_property('7', SolutionCalendarTO, True)

    def add_forwarder_type(self, forwarder_type):
        """Add a forwarder type if not exists."""
        if self.forwarder_types is MISSING:
            self.forwarder_types = []

        if forwarder_type not in self.forwarder_types:
            self.forwarder_types.append(forwarder_type)
            self.inbox_forwarder = True

    def add_calendar(self, calendar):
        """Add a calendar if not exists."""
        if self.calendars is MISSING:
            self.calendars = []

        if not any([calendar.id == c.id for c in self.calendars]):
            self.calendars.append(calendar)
            self.calendar_admin = True


class CustomerSignupTO(object):
    inbox_message_key = unicode_property('1')
    key = unicode_property('2')

    @classmethod
    def from_model(cls, signup):
        to = cls()
        to.inbox_message_key = signup.inbox_message_key
        to.key = unicode(signup.key())
        return to
