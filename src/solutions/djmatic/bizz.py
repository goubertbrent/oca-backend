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

import base64
import hashlib
import json
import logging
from types import NoneType
import urllib

from google.appengine.api import urlfetch, urlfetch_errors
from google.appengine.ext import deferred, db
from mcfw.properties import azzert
from mcfw.rpc import returns, arguments
from rogerthat.bizz.branding import is_branding, BrandingValidationException, TYPE_APP
from rogerthat.bizz.job import run_job
from rogerthat.bizz.messaging import BrandingNotFoundException
from rogerthat.bizz.rtemail import generate_auto_login_url
from rogerthat.bizz.service import QR_TEMPLATE_BLACK_HAND
from rogerthat.dal import put_and_invalidate_cache
from rogerthat.models import ServiceTranslation, ServiceMenuDef
from rogerthat.rpc import users
from rogerthat.service.api import system, qr
from rogerthat.to.service import UserDetailsTO
from rogerthat.utils import generate_random_key, now
from rogerthat.utils.zip_utils import rename_file_in_zip_blob
from solutions import translate
from solutions.common import SOLUTION_COMMON
from solutions.common.bizz import create_solution_service, find_qr_template, SolutionModule, SolutionServiceMenuItem
from solutions.common.bizz.messaging import POKE_TAG_ASK_QUESTION, POKE_TAG_WHEN_WHERE, POKE_TAG_MENU, POKE_TAG_EVENTS, \
    POKE_TAG_NEW_EVENT
from solutions.common.bizz.provisioning import get_and_store_main_branding, get_default_translations, get_and_complete_solution_settings, populate_identity, provision_all_modules, \
    _default_delete, MODULES_GET_APP_DATA_FUNCS, MODULES_PUT_FUNCS, MODULES_DELETE_FUNCS, POKE_TAGS
from solutions.common.dal import get_solution_settings
from solutions.common.models import SolutionSettings, SolutionMainBranding
from solutions.common.to import ProvisionResponseTO
from solutions.djmatic import JUKEBOX_SERVER_API_URL, DEFAULT_LANGUAGES, SOLUTION_DJMATIC
from solutions.djmatic.dal import get_jukebox_app_branding, get_all_djmatic_profile_keys_query, get_djmatic_profile
from solutions.djmatic.handlers import JINJA_ENVIRONMENT
from solutions.djmatic.models import DjMaticProfile, JukeboxAppBranding
from solution_server_settings import get_solution_server_settings


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

MODULE_DJMATIC_JUKEBOX = "DJMATIC_JUKEBOX"

POKE_TAG_JUKEBOX = u"jukebox"
POKE_TAG_QR_CONNECT = u'qr_connect'
BROADCAST_TYPE_KEYS = ['News', 'Events']

TRANSLATION_MAP = {ServiceTranslation.HOME_TEXT: {'jukebox-configuration' : SOLUTION_DJMATIC,
                                                  'ask-question' : SOLUTION_COMMON,
                                                  'when-where' : SOLUTION_COMMON,
                                                  'menu' : SOLUTION_COMMON,
                                                  'agenda' : SOLUTION_COMMON,
                                                  'broadcast-settings' : SOLUTION_COMMON,
                                                },
                   ServiceTranslation.SID_BUTTON: {'get-connected' : SOLUTION_COMMON,
                                                    },
                   ServiceTranslation.BROADCAST_TYPE: { k: SOLUTION_COMMON for k in BROADCAST_TYPE_KEYS}
                   }

MODULE_COORDS_MAPPING = {MODULE_DJMATIC_JUKEBOX: {POKE_TAG_JUKEBOX: {"preferred_page": 0,
                                                                     "coords":[0, 1, 0],
                                                                     "priority":100
                                                                     }},
                         SolutionModule.AGENDA: {POKE_TAG_EVENTS: {"preferred_page": 0,
                                                                   "coords":[0, 2, 0],
                                                                   "priority":10},
                                                 POKE_TAG_NEW_EVENT: {"preferred_page":-1,
                                                                      "coords" :[0, 0, 1],
                                                                      "priority": 1}},
                         SolutionModule.ASK_QUESTION: {POKE_TAG_ASK_QUESTION: {"preferred_page": 0,
                                                                               "coords":[2, 1, 0],
                                                                               "priority":20}},
                         SolutionModule.BROADCAST: {ServiceMenuDef.TAG_MC_BROADCAST_SETTINGS: {"preferred_page": 0,
                                                                                               "coords":[3, 2, 0],
                                                                                               "priority":20}},
                         SolutionModule.BULK_INVITE: None,
                         SolutionModule.MENU: {POKE_TAG_MENU: {"preferred_page": 0,
                                                               "coords":[3, 1, 0],
                                                               "priority":10}},
                         SolutionModule.WHEN_WHERE: {POKE_TAG_WHEN_WHERE: {"preferred_page": 0,
                                                                           "coords":[1, 1, 0],
                                                                           "priority":20}},
                        }


@returns([SolutionServiceMenuItem])
@arguments(sln_settings=SolutionSettings, current_coords=[(int, long)], main_branding=SolutionMainBranding,
           default_lang=unicode, tag=unicode)
def put_djmatic_jukebox(sln_settings, current_coords, main_branding, default_lang, tag):
    service_user = sln_settings.service_user
    djmatic_profile = db.run_in_transaction(get_djmatic_profile, service_user)

    jukebox_branding_hash = djmatic_profile.jukebox_branding_hash
    if not jukebox_branding_hash:
        logging.info("Storing JUKEBOX branding")
        jb_app_branding = get_jukebox_app_branding()
        azzert(jb_app_branding, "No JukeboxAppBranding found!")
        jb_branding_content = base64.b64encode(StringIO(jb_app_branding.blob).read())
        jukebox_branding_hash = system.store_branding(u"Jukebox App", jb_branding_content).id
        djmatic_profile.jukebox_branding_hash = jukebox_branding_hash
        djmatic_profile.put()

    logging.info('Creating WELCOME message flow')
    flow_params = dict(branding_key=main_branding.branding_key, language=default_lang)
    flow = JINJA_ENVIRONMENT.get_template('flows/welcome.xml').render(flow_params)
    welcome_flow = system.put_flow(flow.encode('utf-8'), multilanguage=False)

    if not djmatic_profile.connect_qr_img_url:
        qr_template = find_qr_template(service_user, QR_TEMPLATE_BLACK_HAND)

        connect_qr = qr.create(translate(default_lang, SOLUTION_COMMON, 'get-connected'), POKE_TAG_QR_CONNECT,
                               qr_template, flow=welcome_flow.identifier)
        djmatic_profile.connect_qr_img_url = connect_qr.image_uri
        djmatic_profile.put()

        payload = dict(method="player.updateQrcode", player_id=djmatic_profile.player_id, secret=djmatic_profile.secret,
                       qrcode=connect_qr.image_uri)

        logging.info("Sending request to %s:\n%s" % (JUKEBOX_SERVER_API_URL, payload))
        response = urlfetch.fetch(JUKEBOX_SERVER_API_URL, urllib.urlencode(payload), urlfetch.POST)
        azzert(response.status_code == 200,
               "Got response status code %s and response content: %s" % (response.status_code, response.content))
        logging.info("Got response: %s" % response.content)

    logging.info("Creating JUKEBOX menu item")
    ssmi = SolutionServiceMenuItem(u"djm", sln_settings.menu_item_color,
                                   translate(default_lang, SOLUTION_DJMATIC, 'jukebox-configuration'),
                                   tag, screen_branding=jukebox_branding_hash, run_in_background=False)
    return [ssmi]


@returns(dict)
@arguments(settings=SolutionSettings, service_identity=unicode)
def get_app_data_jukebox(settings, service_identity=None):
    # service_identity is not used but is required for the flex solution
    djmatic_profile = db.run_in_transaction(get_djmatic_profile, settings.service_user)

    player_id = djmatic_profile.player_id
    cMd5 = hashlib.md5()
    cMd5.update(player_id)
    player_id_md5 = cMd5.hexdigest()
    return dict(playerId=player_id,
                playerIdMd5=player_id_md5,
                playerType=djmatic_profile.player_type,
                facebookPageId=settings.facebook_page,
                facebookPageName=settings.facebook_name,
                facebookPageAction=settings.facebook_action,
                description=settings.description)


@returns(NoneType)
@arguments(service_user=users.User)
def provision(service_user):
    logging.debug("Provisioning %s" % service_user)
    users.set_user(service_user)
    try:
        default_lang, _ = get_default_translations(TRANSLATION_MAP)
        sln_settings = get_and_complete_solution_settings(service_user, SOLUTION_DJMATIC)

        djmatic_profile = db.run_in_transaction(get_djmatic_profile, service_user)

        modules_not_for_limited_djmatic_profile = [SolutionModule.AGENDA,
                                                   SolutionModule.ASK_QUESTION,
                                                   SolutionModule.MENU,
                                                   SolutionModule.WHEN_WHERE]
        updated = False
        for module in modules_not_for_limited_djmatic_profile:
            if djmatic_profile.status == DjMaticProfile.STATUS_LIMITED:
                if module in sln_settings.modules:
                    logging.debug("Removing module '%s'", module)
                    sln_settings.modules.remove(module)
                    updated = True
            else:
                if module not in sln_settings.modules:
                    logging.debug("Adding module '%s'", module)
                    sln_settings.modules.append(module)
                    updated = True
        if updated:
            put_and_invalidate_cache(sln_settings)

        main_branding = get_and_store_main_branding(service_user)
        populate_identity(sln_settings, main_branding.branding_key, main_branding.old_branding_key)

        for i, label in enumerate(['About', 'History', 'Call', 'Recommend']):
            system.put_reserved_menu_item_label(i, translate(sln_settings.main_language, SOLUTION_COMMON, label))

        provision_all_modules(sln_settings, MODULE_COORDS_MAPPING, main_branding, default_lang)

        system.put_callback(u"system.api_call", True)
        system.publish_changes()
        logging.info('Service populated!')
    finally:
        users.clear_user()


@returns(ProvisionResponseTO)
@arguments(email=unicode, name=unicode, branding_url=unicode, menu_item_color=unicode, secret=unicode, player_id=unicode, player_type=int)
def create_djmatic_service(email, name, branding_url, menu_item_color, secret, player_id, player_type):
    solution_server_settings = get_solution_server_settings()
    password, solution_settings = create_solution_service(email, name, branding_url, menu_item_color, address=None,
                                                     phone_number=None, solution=SOLUTION_DJMATIC, languages=DEFAULT_LANGUAGES,
                                                     category_id=solution_server_settings.djmatic_category_id, fail_if_exists=False,
                                                     modules=MODULE_COORDS_MAPPING.keys(),
                                                     broadcast_types=BROADCAST_TYPE_KEYS)
    service_user = solution_settings.service_user

    def trans():
        now_ = now()
        djmatic_profile = DjMaticProfile(key=DjMaticProfile.create_key(service_user))
        djmatic_profile.secret = secret
        djmatic_profile.player_id = player_id
        djmatic_profile.player_type = player_type
        djmatic_profile.creation_time = now_
        djmatic_profile.status = DjMaticProfile.STATUS_CREATED
        djmatic_profile.status_history = [DjMaticProfile.STATUS_CREATED]
        djmatic_profile.status_history_epoch = [now_]

        sln_settings = get_solution_settings(service_user)
        sln_settings.search_keywords = u"cafe café jukebox"

        put_and_invalidate_cache(djmatic_profile, sln_settings)

        deferred.defer(provision, service_user, _transactional=True)

        return djmatic_profile

    xg_on = db.create_transaction_options(xg=True)
    djmatic_profile = db.run_in_transaction_options(xg_on, trans)
    logging.info("Created DJMaticProfile: %s", db.to_dict(djmatic_profile))

    resp = ProvisionResponseTO()
    resp.login = email
    resp.password = password
    resp.auto_login_url = generate_auto_login_url(service_user)
    return resp


@returns(unicode)
@arguments(service_user=users.User, user_details=UserDetailsTO)
def register_jukebox(service_user, user_details):
    xmpp_login = u'jukebox_%s' % generate_random_key()[:32]
    xmpp_password = unicode(generate_random_key())

    headers = dict()
    djprof = get_djmatic_profile(service_user)
    payload = dict(method="jukebox.register", player_id=djprof.player_id, secret=djprof.secret,
                   rogerthat_account=u"%s/%s" % (user_details.email, user_details.app_id), xmpp_login=xmpp_login, xmpp_password=xmpp_password)

    logging.info("Sending request to %s:\n%s" % (JUKEBOX_SERVER_API_URL, payload))

    response = do_jukebox_api_call(urllib.urlencode(payload), urlfetch.POST, headers)

    logging.info("Got response: %s" % response.content)

    response = json.loads(response.content)
    azzert(response["error"] is None, response["error"])

    # if the jukebox xmpp account was already created, then the existing xmpp login & password are returned
    xmpp_login = response["result"]["xmpp_login"]
    xmpp_password = response["result"]["xmpp_password"]

    return json.dumps(dict(xmppLogin=xmpp_login, xmppPassword=xmpp_password))


@returns(object)
@arguments(payload=str, method=int, headers=dict)
def do_jukebox_api_call(payload, method, headers):
    attempt = 1
    while True:
        try:
            response = urlfetch.fetch(JUKEBOX_SERVER_API_URL, payload, method, headers)
            azzert(response.status_code == 200, response.content)
            return response
        except urlfetch_errors.Error, e:
            logging.info("do_jukebox_api_call: %s (attempt: %s)", e.__class__, attempt , exc_info=True)
            if attempt >= 5:
                raise e
            attempt += 1

@returns(NoneType)
@arguments(branding_url=unicode)
def add_new_jukebox_app_branding(branding_url):
    resp = urlfetch.fetch(branding_url, deadline=60)
    if resp.status_code != 200:
        raise BrandingNotFoundException()

    # rename branding.html to app.html
    zip_content = rename_file_in_zip_blob(resp.content, "branding.html", "app.html")

    if not is_branding(zip_content, TYPE_APP):
        raise BrandingValidationException("Content of branding download could not be identified as a branding")

    jb_branding = JukeboxAppBranding(key=JukeboxAppBranding.create_key())
    jb_branding.blob = db.Blob(zip_content)
    jb_branding.put()

    run_job(get_all_djmatic_profile_keys_query, [], _reset_jukebox_branding_hash, [])

def _reset_jukebox_branding_hash(djmatic_profile_key):
    def trans():
        djmatic_profile = DjMaticProfile.get(djmatic_profile_key)
        djmatic_profile.jukebox_branding_hash = None
        djmatic_profile.put()

        deferred.defer(provision, djmatic_profile.service_user, _transactional=True)

    xg_on = db.create_transaction_options(xg=True)
    db.run_in_transaction_options(xg_on, trans)


MODULES_GET_APP_DATA_FUNCS[MODULE_DJMATIC_JUKEBOX] = get_app_data_jukebox
MODULES_PUT_FUNCS[MODULE_DJMATIC_JUKEBOX] = put_djmatic_jukebox
MODULES_DELETE_FUNCS[MODULE_DJMATIC_JUKEBOX] = _default_delete
POKE_TAGS[MODULE_DJMATIC_JUKEBOX] = POKE_TAG_JUKEBOX
