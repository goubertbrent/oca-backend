# -*- coding: utf-8 -*-
# Copyright 2016 Mobicage NV
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
# @@license_version:1.1@@

import logging

from google.appengine.ext import db, ndb

from mcfw.cache import CachedModelMixIn, cached
from mcfw.rpc import returns, arguments
from mcfw.serialization import deserializer, ds_model, serializer, s_model, register
from rogerthat.models.common import NdbModel
from rogerthat.models.utils import add_meta
from solutions.common.models import SolutionServiceConsent


class SolutionServerSettings(CachedModelMixIn, db.Model):
    bob_facebook_role_ids = add_meta(db.ListProperty(int, indexed=False),
                                     doc="The facebook id of the users that will be added as administrator on newly created apps (if facebook is enabled)",
                                     order=1)
    bob_api_secret = add_meta(db.StringProperty(indexed=False),
                              doc="The secret used for incoming api request",
                              order=2)


    shop_reply_to_email = add_meta(db.StringProperty(indexed=False),
                                   doc="The email address that is used as reply-to in all e-mails.",
                                   order=301)
    shop_billing_email = add_meta(db.StringProperty(indexed=False),
                                  doc="The email address that is used to send all the e-mails regarding billing",
                                  order=302)
    shop_export_email = add_meta(db.StringProperty(indexed=False),
                                 doc="The email address that is used to send all the e-mails regarding exports",
                                 order=303)
    shop_no_reply_email = add_meta(db.StringProperty(indexed=False),
                                   doc="The email address that is used as reply-to in all no-reply e-mails.",
                                   order=304)
    shop_customer_extention_emails = add_meta(db.StringListProperty(indexed=False),
                                              doc="The email addresses that will receive an email with customers that need extention",
                                              order=306)
    shop_bizz_admin_emails = add_meta(db.StringListProperty(indexed=False),
                                      doc="The email addresses that have admin access to the shop dashboard",
                                      order=307)
    shop_payment_admin_emails = add_meta(db.StringListProperty(indexed=False),
                                         doc="The email addresses that can set the payment status of an order",
                                         order=308)
    shop_new_prospect_sik = add_meta(db.StringProperty(indexed=False),
                                      doc="New prospect sik",
                                      order=310)

    shop_gcs_bucket = add_meta(db.StringProperty(indexed=False), doc='Cloud storage bucket for shop-related files',
                               order=311)

    solution_news_scrapers = add_meta(db.StringListProperty(indexed=False),
                                      doc="News scrapers  (2 entries per combination. eg: - be_loc - test@example.com)",
                                      order=601)
    solution_events_scrapers = add_meta(db.StringListProperty(indexed=False),
                                        doc="Events scrapers  (2 entries per combination. eg: - be_loc - test@example.com)",
                                        order=602)
    solution_qanda_info_receivers = add_meta(db.StringListProperty(indexed=False),
                                             doc="The email addresses that will receive an e-mail when a question has been asked",
                                             order=603)
    solution_service_auto_connect_emails = add_meta(db.StringListProperty(indexed=False),
                                             doc="The email addresses that will be auto connected to new services",
                                             order=604)
    solution_trial_service_email = add_meta(db.StringProperty(indexed=False),
                                            doc="The e-mail address of the yourservcicehere service",
                                            order=605)
    solution_sync_calendar_events_client_id = add_meta(db.StringProperty(indexed=False),
                                            doc="Client id to sync calendar events",
                                            order=607)
    solution_sync_calendar_events_client_secret = add_meta(db.StringProperty(indexed=False),
                                            doc="Client secret to sync calendar events",
                                            order=608)

    tropo_token = add_meta(db.StringProperty(indexed=False),
                           doc="The token used to in api request to tropo",
                           order=1001)
    tropo_callback_token = add_meta(db.StringProperty(indexed=False),
                                    doc="The callback token used in requests from tropo",
                                    order=1002)


    data_be_app_id = add_meta(db.StringProperty(indexed=False),
                              doc="The app_id for data.be",
                              order=1101)
    data_be_app_key = add_meta(db.StringProperty(indexed=False),
                               doc="The app_key for data.be",
                               order=1103)


    twitter_app_key = add_meta(db.StringProperty(indexed=False),
                               doc="The app_key for twitter",
                               order=1201)
    twitter_app_secret = add_meta(db.StringProperty(indexed=False),
                                  doc="The app_secret for twitter",
                                  order=1202)

    facebook_apps = add_meta(db.StringListProperty(indexed=False),
                             doc="Facebook apps (3 entries per app (domain, app id and secret): - www.example.com - 123456789 - aabbccddeeffggeehh123445",
                             order=1301)

    stripe_public_key = add_meta(db.StringProperty(indexed=False),
                                      doc="Stripe public key",
                                      order=1401)
    stripe_secret_key = add_meta(db.StringProperty(indexed=False),
                                      doc="Stripe secret key",
                                      order=1402)

    recaptcha_site_key = add_meta(db.StringProperty(indexed=False),
                                  doc="Google ReCaptcha site key",
                                  order=1501)
    recaptcha_secret_key = add_meta(db.StringProperty(indexed=False),
                                    doc="Google ReCaptcha secret key",
                                    order=1502)

    createsend_api_key = add_meta(db.StringProperty(indexed=False),
                                  doc="Createsend api key",
                                  order=1601)

    joyn_client_id = add_meta(db.StringProperty(indexed=False),
                                  doc="Joyn client_id",
                                  order=1701)
    joyn_client_secret = add_meta(db.StringProperty(indexed=False),
                                  doc="Joyn client_secret",
                                  order=1702)
    participation_server_url = add_meta(db.StringProperty(indexed=False),
                                        doc='Participation server url',
                                        order=1803)
    participation_server_secret = add_meta(db.StringProperty(indexed=False),
                                           doc='Participation server secret, used to create new cities',
                                           order=1804)

    def invalidateCache(self):
        logging.info("SolutionServerSettings removed from cache.")
        get_solution_server_settings.invalidate_cache()


@deserializer
def ds_ss(stream):
    return ds_model(stream, SolutionServerSettings)


@serializer
def s_ss(stream, solution_server_settings):
    s_model(stream, solution_server_settings, SolutionServerSettings)


register(SolutionServerSettings, s_ss, ds_ss)


@cached(1)
@returns(SolutionServerSettings)
@arguments()
def get_solution_server_settings():
    # type: () -> SolutionServerSettings
    @db.non_transactional
    def get():
        ss = SolutionServerSettings.get_by_key_name("MainSettings")
        if not ss:
            ss = SolutionServerSettings(key_name="MainSettings")
        return ss
    return get()


del ds_ss
del s_ss


class CampaignMonitorOrganizationWebhook(NdbModel):
    organization_type = ndb.IntegerProperty()
    list_id = ndb.StringProperty()


class CampaignMonitorWebhook(NdbModel):
    create_date = ndb.DateTimeProperty(indexed=False, auto_now_add=True)
    list_id = ndb.StringProperty()
    consent_type = ndb.StringProperty(choices=SolutionServiceConsent.TYPES)
    organization_lists = ndb.StructuredProperty(CampaignMonitorOrganizationWebhook, repeated=True)  # type: list[CampaignMonitorOrganizationWebhook]

    @property
    def id(self):
        return self.key.id()
    
    def get_organization_lists(self):
        if not self.organization_lists:
            self.organization_lists = []
        return self.organization_lists
    
    def add_organization_list(self, ol):
        self.get_organization_lists().append(ol)

    def get_organization_list(self, organization_type):
        for ol in self.get_organization_lists():
            if ol.organization_type == organization_type:
                return ol
        return None

    @classmethod
    def list_by_list_id(cls, list_id):
        return cls.query().filter(cls.list_id == list_id)

