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

from google.appengine.ext import db

from mcfw.cache import CachedModelMixIn, cached
from mcfw.rpc import returns, arguments
from mcfw.serialization import deserializer, ds_model, serializer, s_model, register
from rogerthat.models.utils import add_meta

import logging


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
    shop_beacons_app_secret = add_meta(db.StringProperty(indexed=False),
                                       doc="The secret used to secure the overriding of a beacon and connecting it to a service (should contain %s 2 times)",
                                       order=305)
    shop_customer_extention_emails = add_meta(db.StringListProperty(indexed=False),
                                              doc="The email addresses that will receive an email with customers that need extention",
                                              order=306)
    shop_bizz_admin_emails = add_meta(db.StringListProperty(indexed=False),
                                      doc="The email addresses that have admin access to the shop dashboard",
                                      order=307)
    shop_payment_admin_emails = add_meta(db.StringListProperty(indexed=False),
                                         doc="The email addresses that can set the payment status of an order",
                                         order=308)
    shop_privacy_policy_url = add_meta(db.StringProperty(indexed=False),
                                      doc="Privacy policy url",
                                      order=309)
    shop_new_prospect_sik = add_meta(db.StringProperty(indexed=False),
                                      doc="New prospect sik",
                                      order=310)


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
    solution_city_wide_lottery = add_meta(db.StringListProperty(indexed=False),
                                          doc="City wide lotteries  (2 entries per combination. eg: - be_loc - 9080",
                                          order=606)
    solution_sync_calendar_events_client_id = add_meta(db.StringProperty(indexed=False),
                                            doc="Client id to sync calendar events",
                                            order=607)
    solution_sync_calendar_events_client_secret = add_meta(db.StringProperty(indexed=False),
                                            doc="Client secret to sync calendar events",
                                            order=608)
    solution_apps_with_news = add_meta(db.StringListProperty(indexed=False),
                                       doc="Apss that have the news feature",
                                       order=609)


    djmatic_service_email = add_meta(db.StringProperty(indexed=False),
                                     doc="The main DJ-Matic service email",
                                     order=901)
    djmatic_secret = add_meta(db.StringProperty(indexed=False),
                              doc="The secret used for incoming api requests",
                              order=902)
    djmatic_overview_emails = add_meta(db.StringListProperty(indexed=False),
                                       doc="The google emails that have access to view and update DJ-Matic statuses",
                                       order=903)
    djmatic_category_id = add_meta(db.StringProperty(indexed=False),
                                   doc="The main DJ-Matic service email",
                                   order=904)


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

    stripe_public_key = add_meta(db.StringProperty(indexed=False),
                                      doc="Stripe public key",
                                      order=1301)
    stripe_secret_key = add_meta(db.StringProperty(indexed=False),
                                      doc="Stripe secret key",
                                      order=1302)


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
    @db.non_transactional
    def get():
        ss = SolutionServerSettings.get_by_key_name("MainSettings")
        if not ss:
            ss = SolutionServerSettings(key_name="MainSettings")
        return ss
    return get()


del ds_ss
del s_ss
