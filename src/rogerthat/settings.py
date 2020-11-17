# -*- coding: utf-8 -*-
# Copyright 2020 Green Valley Belgium NV
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
# @@license_version:1.7@@

import logging

from google.appengine.api import app_identity
from google.appengine.ext import db

from mcfw.cache import CachedModelMixIn, cached
from mcfw.rpc import returns, arguments
from mcfw.serialization import deserializer, ds_model, serializer, s_model, register
from mcfw.utils import chunks
from rogerthat.models.utils import add_meta


class ServerSettings(CachedModelMixIn, db.Model):
    messageFlowRunnerAddress = add_meta(db.StringProperty(indexed=False),
                                        doc="Message flow runner address",
                                        order=5)
    mobidickAddress = add_meta(db.StringProperty(indexed=False),
                               doc="Mobidick address:",
                               order=5)
    secret = add_meta(db.StringProperty(indexed=False),
                      doc="Server secret",
                      order=5)
    baseUrl = add_meta(db.StringProperty(indexed=False),
                       doc="Rogerthat cloud address",
                       order=5)
    webClientUrl = add_meta(db.StringProperty(indexed=False),
                       doc='Web client url',
                       order=6)
    jabberDomain = add_meta(db.StringProperty(indexed=False),
                            doc="Jabber domain",
                            order=10)
    jabberSecret = add_meta(db.StringProperty(indexed=False),
                            doc="Jabber secret",
                            order=10)
    jabberAccountEndPoints = add_meta(db.StringListProperty(indexed=False),
                                      doc="Jabber account endpoints (one ip/port combination per port. eg: 192.168.10.23:8001)",
                                      order=10)
    jabberEndPoints = add_meta(db.StringListProperty(indexed=False),
                               doc="Jabber endpoints (one ip/port combination per port. eg: 192.168.10.23:8001)",
                               order=10)
    jabberBoshEndPoint = add_meta(db.StringProperty(indexed=False),
                                  doc="Jabber bosh endpoint",
                                  order=10)
    dashboardEmail = add_meta(db.StringProperty(indexed=False),
                              doc="Dashboard e-mail address",
                              order=5)
    brandingRendererUrl = add_meta(db.StringProperty(indexed=False),
                                   doc="Branding renderer address",
                                   order=5)
    srvEndPoints = add_meta(db.StringListProperty(indexed=False),
                            doc="DNS SRV records (ip:port:priority. eg: 192.168.10.23:5222:0)",
                            order=11)
    newsServerEndpoints = add_meta(db.StringListProperty(indexed=False),
                                   doc='Used to send realtime updates of news items to the (mobile) clients. records (ip:port)',
                                   order=12)
    newsServerWebhookEndpoint = add_meta(db.StringProperty(indexed=False),
                                         doc='Used to send updates to the news update server (https?://ip:port)',
                                         order=13)
    smtpserverHost = add_meta(db.StringProperty(indexed=False),
                              order=30)
    smtpserverPort = add_meta(db.StringProperty(indexed=False),
                              order=30)
    smtpserverLogin = add_meta(db.StringProperty(indexed=False),
                               order=30)
    smtpserverPassword = add_meta(db.StringProperty(indexed=False),
                                  order=30)
    dkimPrivateKey = add_meta(db.TextProperty(indexed=False),
                              doc="DKIM private key",
                              order=40)
    sendGridApiKey = add_meta(db.TextProperty(indexed=False),
                              doc="SendGrid api key",
                              order=41)

    firebaseKey = add_meta(db.StringProperty(indexed=False), doc="Firebase Cloud Messaging API Key", order=60)
    gcmKey = add_meta(db.StringProperty(indexed=False), doc="Google Cloud Messaging Key", order=61)
    googleMapsKey = add_meta(db.StringProperty(indexed=False), doc="Google Maps Key", order=62)
    googleMapsUrlSigningSecret = add_meta(db.StringProperty(indexed=False), doc='Google Maps Url signing secret. See https://console.cloud.google.com/google/maps-apis/credentials', order=63)

    registrationMainSignature = add_meta(db.StringProperty(indexed=False),
                                         doc="baee64 version of main registration signature", order=80)
    emailHashEncryptionKey = add_meta(db.StringProperty(indexed=False),
                                          doc='Email hash encryption key. Only used for creating apps. No idea why this is needed.',
                                          order=80)
    registrationEmailSignature = add_meta(db.StringProperty(indexed=False),
                                          doc="baee64 version of email registration signature", order=81)
    registrationPinSignature = add_meta(db.StringProperty(indexed=False),
                                        doc="baee64 version of pin registration signature", order=82)

    userCodeCipher = add_meta(db.StringProperty(indexed=False),
                              doc="UserCode cipher (base64.b64encode(SECRET_KEY).decode('utf-8')) and should contain a %s",
                              order=83)

    userEncryptCipherPart1 = add_meta(db.StringProperty(indexed=False),
                                      doc="User encrypt cipher part 1 (base64.b64encode(SECRET_KEY).decode('utf-8'))",
                                      order=84)
    userEncryptCipherPart2 = add_meta(db.StringProperty(indexed=False),
                                      doc="User encrypt cipher part 2 (base64.b64encode(SECRET_KEY).decode('utf-8'))",
                                      order=85)
    cookieSecretKey = add_meta(db.StringProperty(indexed=False),
                               doc="Secret key to encrypt the session (base64.b64encode(SECRET_KEY).decode('utf-8'))",
                               order=86)
    cookieSessionName = add_meta(db.StringProperty(indexed=False), doc="Cookie name for the session", order=87)
    cookieQRScanName = add_meta(db.StringProperty(indexed=False), doc="Cookie name for qr codes", order=88)

    supportEmail = add_meta(db.StringProperty(indexed=False), doc="Main email address to contact support", order=89)
    supportWorkers = add_meta(db.StringListProperty(indexed=False),
                              order=90)

    staticPinCodes = add_meta(db.StringListProperty(indexed=False),
                              doc="Static pin codes  (2 entries per combination. eg: - pincode - test@example.com)",
                              order=93)

    ysaaaMapping = add_meta(db.StringListProperty(indexed=False),
                            doc="YSAAA mapping  (2 entries per combination. eg: - hash - test@example.com)",
                            order=94)

    signupUrl = add_meta(db.StringProperty(indexed=False),
                         doc="Signup URL (e.g. https://example.com/signup)",
                         order=100)
    customSigninPaths = add_meta(db.StringListProperty(indexed=False),
                                 doc="Custom sign in paths based on host name (2 entries per combination. eg: - dashboard.example.com - /user/signin",
                                 order=101)

    firebaseApiKey = add_meta(db.StringProperty(indexed=False),
                              doc='Firebase api key',
                              order=200)
    firebaseAuthDomain = add_meta(db.StringProperty(indexed=False),
                                  doc='Firebase auth domain',
                                  order=201)
    firebaseDatabaseUrl = add_meta(db.StringProperty(indexed=False),
                                   doc='Firebase database URL',
                                   order=202)

    news_statistics_influxdb_host = add_meta(db.StringProperty(indexed=False),
                                             doc='News stats influxdb HOST',
                                             order=301)
    news_statistics_influxdb_port = add_meta(db.IntegerProperty(indexed=False),
                                             doc='News stats influxdb PORT',
                                             order=302)
    news_statistics_influxdb_username = add_meta(db.StringProperty(indexed=False),
                                                 doc='News stats influxdb USER',
                                                 order=304)
    news_statistics_influxdb_password = add_meta(db.StringProperty(indexed=False),
                                                 doc='News stats influxdb PWD',
                                                 order=305)
    news_admin_emails = add_meta(db.StringListProperty(indexed=False),
                                 doc="The email addresses that have admin access to the news dashboard",
                                 order=307)

    mobileFirebaseCredentials = add_meta(db.TextProperty(),
                                         doc='Credentials json file for firebase storage on android and ios',
                                         order=400)

    worker_service_url = add_meta(db.StringProperty(indexed=False),
                                                    doc='Worker service url',
                                                    order=500)

    oca3ApiKey = add_meta(db.StringProperty(indexed=False),
                                            doc='oca-dot-rogerthat-server.ew.r.appspot.com/api api key',
                                            order=501)

    @property
    def senderEmail(self):
        return "Rogerthat Dashboard <%s>" % self.dashboardEmail

    @property
    def senderEmail2ToBeReplaced(self):
        return "Rogerthat Dashboard <rogerthat@%s.appspotmail.com>" % app_identity.get_application_id()

    @property
    def domain(self):
        return self.jabberDomain

    def invalidateCache(self):
        logging.info("ServerSettings removed from cache.")
        get_server_settings.invalidate_cache()

    def get_signin_url(self):
        for url, path in chunks(self.customSigninPaths, 2):
            if path.startswith('/customers/signin'):
                return 'https://%s%s' % (url, path)
        return self.baseUrl


@deserializer
def ds_ss(stream):
    return ds_model(stream, ServerSettings)


@serializer
def s_ss(stream, server_settings):
    s_model(stream, server_settings, ServerSettings)


register(ServerSettings, s_ss, ds_ss)


@cached(1, 3600, read_cache_in_transaction=True)
@returns(ServerSettings)
@arguments()
def get_server_settings():
    # type: () -> ServerSettings
    @db.non_transactional
    def get():
        ss = ServerSettings.get_by_key_name("MainSettings")
        if not ss:
            ss = ServerSettings(key_name="MainSettings")
        return ss

    return get()


del ds_ss
del s_ss
