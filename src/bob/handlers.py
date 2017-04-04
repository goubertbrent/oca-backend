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

import json
import logging

from bob.bizz import set_facebook_app_domain, create_app_from_bob, validate_and_put_main_service, put_app_track
from google.appengine.api import urlfetch
from rogerthat.models import AutoConnectedService
from rogerthat.rpc.service import BusinessException
from rogerthat.to.app import CreateAppRequestTO, FacebookAppDomainTO
from rogerthat.to.beacon import BeaconRegionTO
from rogerthat.translations import localize
from solution_server_settings import get_solution_server_settings
import webapp2


def validate_request(handler):
    solution_server_settings = get_solution_server_settings()
    secret = handler.request.headers.get("X-BOB-SECRET")
    if not solution_server_settings.bob_api_secret:
        logging.error("bob_api_secret is not set yet")
        handler.abort(401)
    if secret != solution_server_settings.bob_api_secret:
        handler.abort(401)

class BobFetchHandler(webapp2.RequestHandler):

    def get(self):
        path = self.request.get('path')
        if not path:
            self.abort(404)

        url = 'https://bob.rogerthat.net%s' % path
        logging.info('Streaming %s', url)
        result = urlfetch.fetch(url, follow_redirects=False, validate_certificate=False, deadline=30)
        if result.status_code == 302:
            logging.info('Redirecting to %s', result.headers['Location'])
            self.response.status = result.status_code
            self.redirect(result.headers['Location'], code=result.status_code)
        elif result.status_code != 200:
            logging.warn('%s %s', url, result.status_code)
            self.abort(404)
        else:
            for k, v in result.headers.iteritems():
                self.response.headers.add_header(k, v)
            self.response.out.write(result.content)


class GetAppsHandler(webapp2.RequestHandler):
    def get(self):
        from shop.models import ShopApp
        validate_request(self)
        self.response.headers['Content-Type'] = 'application/json'
        apps = list()
        for app in ShopApp.all():
            apps.append(dict(name=app.name, id=app.app_id))
        self.response.out.write(json.dumps(apps))


class SetFacebookAppDomain(webapp2.RequestHandler):
    def post(self):
        validate_request(self)
        data = json.loads(self.request.body)
        self.response.headers['Content-Type'] = 'application/json'
        try:
            set_facebook_app_domain(
                data['facebook_app_id'],
                data['facebook_secret'],
                FacebookAppDomainTO.create_for_bob()
            )
            self.response.write(json.dumps(dict(success=True, errormsg=None)))
        except BusinessException, ex:
            self.response.write(json.dumps(dict(success=False, errormsg=ex.message)))


class CreateAppHandler(webapp2.RequestHandler):
    def post(self):
        validate_request(self)
        app = json.loads(self.request.body)
        self.response.headers['Content-Type'] = 'application/json'
        try:
            app_request = CreateAppRequestTO.create(
                app_id=app['app_id'],
                app_name=app['app_name'],
                app_type=app['app_type'],
                facebook_registration_enabled=app['facebook_registration_enabled'],
                facebook_app_id=app['facebook_app_id'],
                facebook_secret=app['facebook_secret'],
                facebook_user_access_token=app['facebook_user_access_token'],
                dashboard_email_address=app['dashboard_email_address'],
                core_branding=app['core_branding'],
                qr_template_type=app['qr_template'],
                custom_qr_template=app['custom_qr_template'],
                custom_qr_template_color=app['custom_qr_template_color'],
                auto_connected_services=[AutoConnectedService.create(acs['email'], acs['removable'], [], [])
                                         for acs in app['auto_connected_services']],
                orderable_apps=app['orderable_apps'],
                beacon_regions_to=[BeaconRegionTO.create(b_region['uuid'], b_region['major'], b_region['minor']) for
                                   b_region in app['beacon_regions']]
            )
            create_app_from_bob(app_request)
            self.response.write(json.dumps(dict(success=True, errormsg=None)))
        except BusinessException, ex:
            self.response.write(json.dumps(dict(success=False, errormsg=ex.message)))


class BobTranslationsHandler(webapp2.RequestHandler):
    def post(self):
        validate_request(self)
        data = json.loads(self.request.body)
        lang = data['language']
        self.response.headers['Content-Type'] = 'application/json'
        translations = dict()
        for trans in data['translations']:
            key = trans['key']
            translations[key] = localize(lang, key, **trans['args'])
        self.response.write(json.dumps(dict(success=True, errormsg=None, translations=translations)))


class BobPutMainService(webapp2.RequestHandler):
    def post(self):
        validate_request(self)
        data = json.loads(self.request.body)
        app_id = data['app_id']
        main_service_email = data['main_service_email']
        self.response.headers['Content-Type'] = 'application/json'
        try:
            warning = validate_and_put_main_service(app_id, main_service_email)
            self.response.write(json.dumps(dict(success=True, errormsg=None, warning=warning)))
        except BusinessException, exception:
            self.response.write(json.dumps(dict(success=False, errormsg=exception.message)))


class BobPutAppTrack(webapp2.RequestHandler):
    def post(self):
        validate_request(self)
        data = json.loads(self.request.body)
        app_id = data['app_id']
        playstore_track = data['playstore_track']
        self.response.headers['Content-Type'] = 'application/json'
        try:
            put_app_track(app_id, playstore_track)
            self.response.write(json.dumps(dict(success=True, errormsg=None)))
        except BusinessException, exception:
            self.response.write(json.dumps(dict(success=False, errormsg=exception.message)))
