# -*- coding: utf-8 -*-
# Copyright 2019 Green Valley Belgium NV
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

import urllib

from google.appengine.api import images
from google.appengine.ext import db, blobstore, ndb

from rogerthat.bizz.gcs import get_serving_url
from rogerthat.dal import parent_key, parent_key_unsafe, parent_ndb_key
from rogerthat.models import ArchivedModel, NdbModel
from rogerthat.rpc import users
from rogerthat.utils import now
from rogerthat.utils.app import create_app_user_by_email
from rogerthat.utils.crypto import sha256_hex
from rogerthat.utils.service import get_identity_from_service_identity_user, \
    get_service_user_from_service_identity_user
from solutions.common import SOLUTION_COMMON
from solutions.common.models.properties import SolutionUserProperty
from solutions.common.utils import create_service_identity_user_wo_default


class SolutionLoyaltySlide(db.Model):
    timestamp = db.IntegerProperty()
    name = db.StringProperty(indexed=False)
    time = db.IntegerProperty(indexed=False)
    item = blobstore.BlobReferenceProperty()
    gcs_filename = db.StringProperty(indexed=False)
    content_type = db.StringProperty(indexed=False)
    deleted = db.BooleanProperty(default=False)

    @property
    def id(self):
        return self.key().id()

    @property
    def function_dependencies(self):
        return 0

    def item_url(self):
        if self.gcs_filename:
            k = blobstore.create_gs_key('/gs' + self.gcs_filename)
        else:
            k = self.item
        return unicode(images.get_serving_url(k, secure_url=True))

    def slide_url(self):
        from rogerthat.settings import get_server_settings
        server_settings = get_server_settings()
        if self.gcs_filename:
            return get_serving_url(self.gcs_filename)
        return unicode("%s/unauthenticated/loyalty/slide?%s" % (server_settings.baseUrl, urllib.urlencode(dict(slide_key=self.item.key()))))

    @property
    def service_identity_user(self):
        return users.User(self.parent_key().name())

    @property
    def service_user(self):
        return get_service_user_from_service_identity_user(self.service_identity_user)

    @property
    def service_identity(self):
        return get_identity_from_service_identity_user(self.service_identity_user)


class SolutionLoyaltyVisitRevenueDiscount(db.Model, ArchivedModel):
    app_user = db.UserProperty()
    app_user_info = SolutionUserProperty()

    admin_user = db.UserProperty()
    timestamp = db.IntegerProperty()

    redeemed = db.BooleanProperty(default=False)
    redeemed_admin_user = db.UserProperty()
    redeemed_timestamp = db.IntegerProperty()

    price = db.IntegerProperty(indexed=False)  # in euro cents

    @property
    def key_str(self):
        return str(self.key())

    @property
    def loyalty_type(self):
        return SolutionLoyaltySettings.LOYALTY_TYPE_REVENUE_DISCOUNT

    @property
    def service_identity_user(self):
        return users.User(self.parent_key().name())

    @property
    def service_user(self):
        return get_service_user_from_service_identity_user(self.service_identity_user)

    @property
    def service_identity(self):
        return get_identity_from_service_identity_user(self.service_identity_user)

    @property
    def price_in_euro(self):
        return '{:0,.2f}'.format(self.price / 100.0)

    def discount_in_euro(self, x_discount):
        return '{:0,.2f}'.format(self.price * x_discount / 10000.0)

    @classmethod
    def load(cls, service_user, service_identity):
        service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
        qry = cls.all().ancestor(parent_key_unsafe(service_identity_user, SOLUTION_COMMON))
        qry.filter('redeemed', False)
        qry.order('-timestamp')
        return qry

    @classmethod
    def get_for_time_period(cls, service_user, service_identity, first_day, last_day):
        service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
        return cls.all() \
            .ancestor(parent_key_unsafe(service_identity_user, SOLUTION_COMMON)) \
            .filter('redeemed_timestamp >=', first_day) \
            .filter('redeemed_timestamp <', last_day)


class SolutionLoyaltyVisitRevenueDiscountArchive(SolutionLoyaltyVisitRevenueDiscount):
    pass

class SolutionLoyaltyVisitLottery(db.Model, ArchivedModel):
    app_user = db.UserProperty()
    app_user_info = SolutionUserProperty()

    admin_user = db.UserProperty()
    timestamp = db.IntegerProperty()

    redeemed = db.BooleanProperty(default=False)
    redeemed_timestamp = db.IntegerProperty()

    @property
    def key_str(self):
        return str(self.key())

    @property
    def timestamp_day(self):
        return long(self.key().name().split("|")[0])

    @property
    def loyalty_type(self):
        return SolutionLoyaltySettings.LOYALTY_TYPE_LOTTERY

    @property
    def service_identity_user(self):
        return users.User(self.parent_key().name())

    @property
    def service_user(self):
        return get_service_user_from_service_identity_user(self.service_identity_user)

    @property
    def service_identity(self):
        return get_identity_from_service_identity_user(self.service_identity_user)

    @classmethod
    def load(cls, service_user, service_identity):
        service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
        qry = cls.all().ancestor(parent_key_unsafe(service_identity_user, SOLUTION_COMMON))
        qry.filter('redeemed =', False)
        qry.order('-timestamp')
        return qry

    @classmethod
    def create_key(cls, service_user, service_identity, app_user, timestamp_day):
        service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
        return db.Key.from_path(cls.kind(), "%s|%s" % (timestamp_day, app_user.email()), parent=parent_key_unsafe(service_identity_user, SOLUTION_COMMON))


class SolutionLoyaltyVisitLotteryArchive(SolutionLoyaltyVisitLottery):
    pass

class SolutionLoyaltyVisitStamps(db.Model, ArchivedModel):
    app_user = db.UserProperty()
    app_user_info = SolutionUserProperty()

    admin_user = db.UserProperty()
    timestamp = db.IntegerProperty()

    redeemed = db.BooleanProperty(default=False)
    redeemed_admin_user = db.UserProperty()
    redeemed_timestamp = db.IntegerProperty()

    count = db.IntegerProperty()
    x_stamps = db.IntegerProperty(indexed=False)
    winnings = db.TextProperty()

    @property
    def key_str(self):
        return str(self.key())

    @property
    def loyalty_type(self):
        return SolutionLoyaltySettings.LOYALTY_TYPE_STAMPS

    @property
    def service_identity_user(self):
        return users.User(self.parent_key().name())

    @property
    def service_user(self):
        return get_service_user_from_service_identity_user(self.service_identity_user)

    @property
    def service_identity(self):
        return get_identity_from_service_identity_user(self.service_identity_user)

    @classmethod
    def load(cls, service_user, service_identity):
        service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
        qry = cls.all().ancestor(parent_key_unsafe(service_identity_user, SOLUTION_COMMON))
        qry.filter('redeemed', False)
        qry.order('-timestamp')
        return qry

    @classmethod
    def get_for_time_period(cls, service_user, service_identity, first_day, last_day):
        service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
        return cls.all() \
            .ancestor(parent_key_unsafe(service_identity_user, SOLUTION_COMMON)) \
            .filter('redeemed_timestamp >=', first_day) \
            .filter('redeemed_timestamp <', last_day)


class SolutionLoyaltyVisitStampsArchive(SolutionLoyaltyVisitStamps):
    pass


class SolutionLoyaltyIdentitySettings(db.Model):
    admins = db.StringListProperty(indexed=False)
    app_ids = db.StringListProperty(indexed=False)
    names = db.StringListProperty(indexed=False)
    functions = db.ListProperty(int, indexed=False)
    name_index = db.IntegerProperty(indexed=False)

    image_uri = db.StringProperty(indexed=False)
    content_uri = db.StringProperty(indexed=False)

    @staticmethod
    def create_key(service_user, service_identity):
        service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
        return db.Key.from_path(SolutionLoyaltyIdentitySettings.kind(), service_identity_user.email(),
                                parent=parent_key_unsafe(service_identity_user, SOLUTION_COMMON))

    @classmethod
    def get_by_user(cls, service_user, service_identity):
        return cls.get(cls.create_key(service_user, service_identity))


class SolutionLoyaltySettings(SolutionLoyaltyIdentitySettings):
    LOYALTY_TYPE_REVENUE_DISCOUNT = 1
    LOYALTY_TYPE_LOTTERY = 2
    LOYALTY_TYPE_STAMPS = 3
    LOYALTY_TYPE_CITY_WIDE_LOTTERY = 4
    LOYALTY_TYPE_SLIDES_ONLY = 5

    LOYALTY_TYPE_MAPPING = {LOYALTY_TYPE_REVENUE_DISCOUNT: SolutionLoyaltyVisitRevenueDiscount,
                            LOYALTY_TYPE_LOTTERY: SolutionLoyaltyVisitLottery,
                            LOYALTY_TYPE_STAMPS: SolutionLoyaltyVisitStamps}

    FUNCTION_SCAN = 1
    FUNCTION_SLIDESHOW = 2
    FUNCTION_ADD_REDEEM_LOYALTY_POINTS = 4

    loyalty_type = db.IntegerProperty(default=LOYALTY_TYPE_REVENUE_DISCOUNT)

    website = db.StringProperty(indexed=False)

    branding_key = db.StringProperty(indexed=False)  # rogerthat branding key
    branding_creation_time = db.IntegerProperty(default=0, indexed=False)
    modification_time = db.IntegerProperty(default=0, indexed=False)

    # LOYALTY_TYPE_REVENUE_DISCOUNT
    x_visits = db.IntegerProperty(indexed=False, default=10)
    x_discount = db.IntegerProperty(indexed=False, default=5)

    # LOYALTY_TYPE_LOTTERY has its own model

    # LOYALTY_TYPE_STAMPS
    x_stamps = db.IntegerProperty(indexed=False, default=8)
    stamps_type = db.IntegerProperty(indexed=False, default=1)
    stamps_winnings = db.TextProperty()
    stamps_auto_redeem = db.BooleanProperty(indexed=False, default=False)

    @property
    def service_user(self):
        return users.User(self.parent_key().name())

    @classmethod
    def create_key(cls, service_user):
        return db.Key.from_path(cls.kind(), service_user.email(), parent=parent_key(service_user, SOLUTION_COMMON))

    @classmethod
    def get_by_user(cls, service_user):
        return cls.get(cls.create_key(service_user))

class SolutionUserLoyaltySettings(db.Model):

    reminders_disabled = db.BooleanProperty(indexed=False, default=False)
    reminders_disabled_for = db.StringListProperty(indexed=False)

    @property
    def app_user(self):
        return users.User(self.parent_key().name())

    @classmethod
    def createKey(cls, app_user):
        return db.Key.from_path(cls.kind(), app_user.email(), parent=parent_key(app_user, SOLUTION_COMMON))

    @classmethod
    def get_by_user(cls, app_user):
        return cls.get(cls.createKey(app_user))


class SolutionLoyaltyScan(db.Model):
    tablet_email = db.StringProperty(indexed=False)
    tablet_app_id = db.StringProperty(indexed=False)
    tablet_name = db.StringProperty(indexed=False)
    user_name = db.StringProperty(indexed=False)
    timestamp = db.IntegerProperty()
    processed = db.BooleanProperty(default=False)

    app_user_info = SolutionUserProperty()

    @property
    def key_str(self):
        return str(self.key())

    @property
    def admin_user(self):
        return create_app_user_by_email(self.tablet_email, self.tablet_app_id)

    @property
    def app_user(self):
        return users.User(self.key().name())

    @property
    def service_identity_user(self):
        return users.User(self.parent_key().name())

    @property
    def service_user(self):
        return get_service_user_from_service_identity_user(self.service_identity_user)

    @property
    def service_identity(self):
        return get_identity_from_service_identity_user(self.service_identity_user)

    @classmethod
    def create_key(cls, app_user, service_user, service_identity):
        service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
        return db.Key.from_path(cls.kind(), app_user.email(), parent=parent_key_unsafe(service_identity_user, SOLUTION_COMMON))

    @classmethod
    def get_by_service_user(cls, service_user, service_identity):
        service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
        return cls.all().ancestor(parent_key_unsafe(service_identity_user, SOLUTION_COMMON)).filter("processed =", False).filter("timestamp >", now() - (60 * 60 * 24)).order("timestamp")

class SolutionLoyaltyLottery(db.Model):
    schedule_loot_time = db.IntegerProperty()
    timestamp = db.IntegerProperty()
    end_timestamp = db.IntegerProperty()
    winnings = db.TextProperty()

    winner = db.UserProperty()  # app_user
    winner_info = SolutionUserProperty()
    winner_timestamp = db.IntegerProperty()
    skip_winners = db.ListProperty(users.User, indexed=False)

    solution_inbox_message_key = db.StringProperty(indexed=False)
    deleted = db.BooleanProperty(default=False)
    pending = db.BooleanProperty(default=False)
    redeemed = db.BooleanProperty(default=False)
    claimed = db.BooleanProperty(default=False)

    count = db.ListProperty(int, indexed=False)  # this will be filled in when the lottery is redeemed
    app_users = db.ListProperty(users.User, indexed=False)  # this will be filled in when the lottery is redeemed

    @property
    def key_str(self):
        return str(self.key())

    @property
    def service_identity_user(self):
        return users.User(self.parent_key().name())

    @property
    def service_user(self):
        return get_service_user_from_service_identity_user(self.service_identity_user)

    @property
    def service_identity(self):
        return get_identity_from_service_identity_user(self.service_identity_user)

    @classmethod
    def load_all(cls, service_user, service_identity):
        service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
        qry = cls.all().ancestor(parent_key_unsafe(service_identity_user, SOLUTION_COMMON))
        qry.filter('deleted =', False)
        return qry

    @classmethod
    def load_active(cls, service_user, service_identity):
        service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
        qry = cls.all().ancestor(parent_key_unsafe(service_identity_user, SOLUTION_COMMON))
        qry.filter('deleted =', False)
        qry.filter('redeemed =', False)
        return qry

    @classmethod
    def load_pending(cls, service_user, service_identity):
        service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
        qry = cls.all().ancestor(parent_key_unsafe(service_identity_user, SOLUTION_COMMON))
        qry.filter('deleted =', False)
        qry.filter('pending =', True)
        qry.order("end_timestamp")
        return qry.get()

    @classmethod
    def get_for_time_period(cls, service_user, service_identity, first_day, last_day):
        service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
        return cls.all() \
            .ancestor(parent_key_unsafe(service_identity_user, SOLUTION_COMMON)) \
            .filter('winner_timestamp >', first_day) \
            .filter('winner_timestamp <', last_day) \
            .filter('deleted =', False) \
            .filter('claimed', True)


class SolutionLoyaltyLotteryStatistics(db.Model):
    count = db.ListProperty(int, indexed=False)
    app_users = db.ListProperty(users.User, indexed=False)

    @property
    def service_identity_user(self):
        return users.User(self.parent_key().name())

    @property
    def service_user(self):
        return get_service_user_from_service_identity_user(self.service_identity_user)

    @property
    def service_identity(self):
        return get_identity_from_service_identity_user(self.service_identity_user)

    @classmethod
    def create_key(cls, service_user, service_identity):
        service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
        return db.Key.from_path(cls.kind(), service_user.email(), parent=parent_key_unsafe(service_identity_user, SOLUTION_COMMON))

    @classmethod
    def get_by_user(cls, service_user, service_identity):
        return cls.get(cls.create_key(service_user, service_identity))


class SolutionLoyaltyExport(db.Model):
    pdf = db.BlobProperty()
    year_month = db.IntegerProperty()  # 201511

    @property
    def service_identity_user(self):
        return users.User(self.parent_key().name())

    @property
    def service_user(self):
        return get_service_user_from_service_identity_user(self.service_identity_user)

    @property
    def service_identity(self):
        return get_identity_from_service_identity_user(self.service_identity_user)

    @classmethod
    def create_key(cls, service_user, service_identity, year, month):
        service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
        return db.Key.from_path(cls.kind(), '%s_%s' % (year, month), parent=parent_key_unsafe(service_identity_user, SOLUTION_COMMON))

    @classmethod
    def list_by_service_user(cls, service_user, service_identity):
        service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
        return cls.all().ancestor(parent_key_unsafe(service_identity_user, SOLUTION_COMMON)).order('-year_month')


class SolutionCityWideLotteryVisit(db.Model):
    original_visit_key = db.StringProperty(indexed=True)
    original_loyalty_type = db.IntegerProperty(indexed=False)
    app_user = db.UserProperty()
    app_user_info = SolutionUserProperty()

    timestamp = db.IntegerProperty(indexed=True)
    redeemed = db.BooleanProperty(indexed=True)
    redeemed_timestamp = db.IntegerProperty(indexed=False)

    @property
    def key_str(self):
        return str(self.key())

    @property
    def loyalty_type(self):
        return SolutionLoyaltySettings.LOYALTY_TYPE_LOTTERY

    @property
    def service_identity_user(self):
        return users.User(self.parent_key().name())

    @property
    def service_user(self):
        return get_service_user_from_service_identity_user(self.service_identity_user)

    @property
    def service_identity(self):
        return get_identity_from_service_identity_user(self.service_identity_user)

    @property
    def app_id(self):
        return self.parent_key().parent().name()

    @property
    def timestamp_day(self):
        return self.timestamp - (self.timestamp % (3600 * 24))

    @classmethod
    def create_city_parent_key(cls, app_id):
        return db.Key.from_path(u"city_wide_lottery", app_id)

    @classmethod
    def create_parent_key(cls, app_id, service_user, service_identity, app_user):
        service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
        city_ancestor_key = cls.create_city_parent_key(app_id)
        service_ancestor_key = db.Key.from_path(SOLUTION_COMMON, service_identity_user.email(), parent=city_ancestor_key)
        return db.Key.from_path(cls.kind(), app_user.email(), parent=service_ancestor_key)

    @classmethod
    def list_by_app_id(cls, app_id):
        city_ancestor_key = cls.create_city_parent_key(app_id)
        return cls.all().ancestor(city_ancestor_key).filter('redeemed =', False)

    @classmethod
    def get_visit_by_original_visit_key(cls, app_id, service_user, service_identity, app_user, visit_key):
        parent_key = cls.create_parent_key(app_id, service_user, service_identity, app_user)
        return cls.all().ancestor(parent_key).filter("original_visit_key =", visit_key).get()

    @classmethod
    def load(cls, app_id):
        city_ancestor_key = cls.create_city_parent_key(app_id)
        qry = cls.all().ancestor(city_ancestor_key)
        qry.filter("redeemed =", False)
        qry.order('-timestamp')
        return qry


class SolutionCityWideLottery(db.Model):
    schedule_loot_time = db.IntegerProperty()
    timestamp = db.IntegerProperty()
    end_timestamp = db.IntegerProperty()
    winnings = db.TextProperty()

    x_winners = db.IntegerProperty(indexed=False, default=1)
    winners = db.ListProperty(users.User, indexed=False)  # app_user
    winners_info = db.TextProperty()  # json [ExtendedUserDetailsTO]
    skip_winners = db.ListProperty(users.User, indexed=False)

    deleted = db.BooleanProperty(default=False)
    pending = db.BooleanProperty(default=False)

    count = db.ListProperty(int, indexed=False)  # this will be filled in when the lottery is redeemed
    app_users = db.ListProperty(users.User, indexed=False)  # this will be filled in when the lottery is redeemed

    @property
    def key_str(self):
        return str(self.key())

    @property
    def app_id(self):
        return self.parent_key().name()

    @classmethod
    def create_parent_key(cls, app_id):
        return db.Key.from_path(u"city_wide_lottery", app_id)

    @classmethod
    def load_all(cls, app_id):
        qry = cls.all().ancestor(cls.create_parent_key(app_id))
        qry.filter('deleted =', False)
        return qry

    @classmethod
    def load_pending(cls, app_id):
        qry = cls.all().ancestor(cls.create_parent_key(app_id))
        qry.filter('deleted =', False)
        qry.filter('pending =', True)
        qry.order("end_timestamp")
        return qry.get()


class SolutionCityWideLotteryStatistics(db.Model):
    count = db.ListProperty(int, indexed=False)
    app_users = db.ListProperty(users.User, indexed=False)

    @classmethod
    def create_key(cls, app_id):
        parent_key = db.Key.from_path(SOLUTION_COMMON, app_id)
        return db.Key.from_path(cls.kind(), app_id, parent=parent_key)

    @classmethod
    def get_by_app_id(cls, app_id):
        return cls.get(cls.create_key(app_id))


class CustomLoyaltyCard(db.Model):
    TYPE = u'custom_loyalty_card'

    # The unknown QR which is used by the enduser
    custom_qr_content = db.TextProperty(required=True)

    # The loyalty QR which is created by Rogerthat-backend when coupling the custom loyalty card
    loyalty_qr_content = db.StringProperty(indexed=False, required=True)
    creation_time = db.DateTimeProperty(auto_now_add=True, indexed=False)

    # The email:app_id of the enduser
    app_user = db.UserProperty(indexed=False, required=True)

    @classmethod
    def get_by_url(cls, url):
        return cls.get(cls.create_key(url))

    @classmethod
    def create_key(cls, url):
        return db.Key.from_path(cls.kind(), sha256_hex(url))


class CityPostalCodes(db.Model):
    app_id = db.StringProperty(indexed=False)
    postal_codes = db.StringListProperty(indexed=False)

    @classmethod
    def create_key(cls, app_id):
        return db.Key.from_path(cls.kind(), app_id)
