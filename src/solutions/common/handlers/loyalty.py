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

import base64
from cgi import FieldStorage
import datetime
import json
import logging

import cloudstorage
from google.appengine.ext import db, webapp
from mcfw.properties import azzert
from rogerthat.bizz.gcs import get_blobstore_cloudstorage_path, upload_to_gcs
from rogerthat.bizz.user import calculate_secure_url_digest
from rogerthat.consts import ROGERTHAT_ATTACHMENTS_BUCKET
from rogerthat.dal import parent_key_unsafe
from rogerthat.models import UserProfile
from rogerthat.rpc import users
from rogerthat.settings import get_server_settings
from rogerthat.translations import DEFAULT_LANGUAGE
from rogerthat.utils.channel import broadcast_via_iframe_result
from rogerthat.utils.crypto import decrypt
from rogerthat.utils.service import get_service_identity_tuple, create_service_identity_user
from solutions import translate as common_translate
from solutions.common import SOLUTION_COMMON
from solutions.common.bizz import SolutionModule
from solutions.common.bizz.loyalty import put_loyalty_slide, get_loyalty_slide_footer, redeem_lottery_winners
from solutions.common.dal import get_solution_settings
from solutions.common.handlers import JINJA_ENVIRONMENT
from solutions.common.models import SolutionInboxMessage
from solutions.common.models.loyalty import SolutionLoyaltySlide, SolutionLoyaltyExport, SolutionUserLoyaltySettings
from solutions.common.utils import is_default_service_identity, create_service_identity_user_wo_default, \
    get_extension_for_content_type
import webapp2


class UploadLoyaltySlideHandler(webapp2.RequestHandler):

    def post(self):
        service_user = users.get_current_user()
        session_ = users.get_current_session()
        service_identity = session_.service_identity
        slide_id = self.request.get("slide_id", "")
        if slide_id == "":
            slide_id = None
        else:
            slide_id = long(slide_id)
        slide_name = self.request.get("slide_name", "")

        try:
            slide_time = long(self.request.get("slide_time", 10))
        except:
            self.response.out.write(broadcast_via_iframe_result(u"solutions.common.loyalty.slide.post_result",
                                                                    error=u"Please fill in valid time!"))
            return

        uploaded_file = self.request.POST.get('slide_file')  # type: FieldStorage
        if not slide_id and not isinstance(uploaded_file, FieldStorage):
            self.response.out.write(broadcast_via_iframe_result(u"solutions.common.loyalty.slide.post_result",
                                                                    error=u"Please select a picture!"))
            return

        if not slide_id:
            sln_settings = get_solution_settings(service_user)
            if SolutionModule.HIDDEN_CITY_WIDE_LOTTERY in sln_settings.modules:
                service_identity_user = create_service_identity_user_wo_default(service_user, service_identity)
                p = parent_key_unsafe(service_identity_user, SOLUTION_COMMON)
                sli = SolutionLoyaltySlide.all(keys_only=True).ancestor(p).get()
                if sli:
                    self.response.out.write(broadcast_via_iframe_result(u"solutions.common.loyalty.slide.post_result",
                                                                    error=u"A city can only have 1 active slide at a time!"))
                    return

        gcs_filename = None
        content_type = None
        if isinstance(uploaded_file, FieldStorage):
            content_type = uploaded_file.type
            if not content_type.startswith("image/"):
                self.response.out.write(broadcast_via_iframe_result(u"solutions.common.loyalty.slide.post_result",
                                                                        error=u"The uploaded file is not an image!"))
                return

            date = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
            gcs_filename = '%s/oca/loyalty_slides/%s/%s_%s.%s' % (ROGERTHAT_ATTACHMENTS_BUCKET,
                                                               service_user.email(),
                                                               date,
                                                               uploaded_file.filename,
                                                               get_extension_for_content_type(content_type))
            upload_to_gcs(uploaded_file.value, content_type, gcs_filename)

        put_loyalty_slide(service_user, service_identity, slide_id, slide_name, slide_time, gcs_filename, content_type)

        self.response.out.write(broadcast_via_iframe_result(u"solutions.common.loyalty.slide.post_result"))


class LoyaltySlideDownloadHandler(webapp2.RequestHandler):
    def get(self):
        key = self.request.get("slide_key", None)
        filename = get_blobstore_cloudstorage_path(key)

        try:
            gcs_stats = cloudstorage.stat(filename)
            self.response.headers['Content-Type'] = gcs_stats.content_type
            self.response.headers['Cache-Control'] = 'public, max-age=31536000'  # Cache forever (1 year)
            self.response.headers['Content-Disposition'] = 'inline; filename=%s' % str(key)
            with cloudstorage.open(filename, 'r') as gcs_file:
                self.response.write(gcs_file.read())

        except cloudstorage.errors.NotFoundError:
            logging.warn('%s NOT found in gcs', filename)
            self.error(404)


class LoyaltySlidePreviewHandler(webapp2.RequestHandler):

    def get(self):
        service_user = users.get_current_user()
        session_ = users.get_current_session()
        service_identity = session_.service_identity
        slide_id = self.request.get('i')
        if not slide_id:
            self.redirect("/ourcityapp")
            return
        slide_id = long(slide_id)
        if is_default_service_identity(service_identity):
            service_identity_user = service_user
        else:
            service_identity_user = create_service_identity_user(service_user, service_identity)
        def trans():
            slide = SolutionLoyaltySlide.get_by_id(slide_id, parent=parent_key_unsafe(service_identity_user, SOLUTION_COMMON))
            return slide
        slide = db.run_in_transaction(trans)
        if not slide:
            self.redirect("/ourcityapp")
            return
        server_settings = get_server_settings()
        jinja_template = JINJA_ENVIRONMENT.get_template('loyalty_preview.html')
        self.response.out.write(jinja_template.render({'slide_id': slide_id,
                                                       'full_url': slide.slide_url(),
                                                       'overlay_url': '%s/common/loyalty/slide/overlay' % (server_settings.baseUrl)}))

class LoyaltySlideOverlayHandler(webapp2.RequestHandler):

    def get(self):
        self.response.headers['Cache-Control'] = "public, max-age=31536000"  # Cache forever (1 year)
        self.response.headers['Content-Type'] = "image/png"
        self.response.out.write(get_loyalty_slide_footer())


class ExportLoyaltyHandler(webapp2.RequestHandler):
    def get(self):
        service_user = users.get_current_user()
        session_ = users.get_current_session()
        service_identity = session_.service_identity
        year = self.request.get('y')
        month = self.request.get('m')
        export = SolutionLoyaltyExport.get(SolutionLoyaltyExport.create_key(service_user, service_identity, year, month))
        if export:
            self.response.headers['Content-Type'] = 'application/pdf'
            self.response.headers['Content-Disposition'] = str(
                'attachment; filename=loyalty_export %s-%s.pdf' % (month, year))
            self.response.write(export.pdf)
            self.response.set_status(200)
        else:
            self.response.set_status(404)


class LoyaltyNoMobilesUnsubscribeEmailHandler(webapp.RequestHandler):

    def parse_data(self, email, data):
        user = users.User(email)
        data = base64.decodestring(data)
        data = decrypt(user, data)
        data = json.loads(data)
        azzert(data["d"] == calculate_secure_url_digest(data))
        return data, user

    def get_user_info(self):
        email = self.request.get("email", None)
        data = self.request.get("data", None)

        if not email or not data:
            return None, None

        try:
            data_dict, _ = self.parse_data(email, data)
        except:
            logging.warn("Could not decipher url!", exc_info=True)
            return None, None

        app_user = users.User(email)
        return data_dict, app_user


    def get(self):
        data_dict, app_user = self.get_user_info()
        if not data_dict or not app_user:
            language = self.request.get("language", DEFAULT_LANGUAGE)
            title = common_translate(language, u'Error')
            text = common_translate(language, u"error-occured-unknown-try-again")
        else:
            azzert(data_dict['a'] == "loyalty_no_mobiles_unsubscribe")
            service_name = data_dict['n']
            service_identity_user_email = data_dict['e']

            suls_key = SolutionUserLoyaltySettings.createKey(app_user)
            suls = SolutionUserLoyaltySettings.get(suls_key)
            if not suls:
                suls = SolutionUserLoyaltySettings(key=suls_key)
                suls.reminders_disabled = False
                suls.reminders_disabled_for = []

            if service_identity_user_email not in suls.reminders_disabled_for:
                suls.reminders_disabled_for.append(service_identity_user_email)
                suls.put()

            user_profile = db.get(UserProfile.createKey(app_user))
            if user_profile:
                language = self.request.get("language", user_profile.language)
            else:
                language = self.request.get("language", DEFAULT_LANGUAGE)

            title = common_translate(language, u'You have been unsubscribed')
            text = common_translate(language, u'You will not receive any loyalty updates from "%(name)s" anymore', name=service_name)

        params = {
            'title': title,
            'text': text
        }

        jinja_template = JINJA_ENVIRONMENT.get_template('pages/loyalty_title_text.html')
        self.response.out.write(jinja_template.render(params))

class LoyaltyLotteryConfirmWinnerHandler(LoyaltyNoMobilesUnsubscribeEmailHandler):

    def get(self):
        data_dict, app_user = self.get_user_info()
        if not data_dict or not app_user:
            language = self.request.get("language", DEFAULT_LANGUAGE)
            title = common_translate(language, u'Error')
            text = common_translate(language, u"error-occured-unknown-try-again")
        else:
            azzert(data_dict['a'] == "loyalty_no_mobiles_lottery_winner")
            service_email = data_dict['e']
            service_identity_user = users.User(service_email)
            service_user, service_identity = get_service_identity_tuple(service_identity_user)
            user_profile = db.get(UserProfile.createKey(app_user))
            if user_profile:
                language = self.request.get("language", user_profile.language)
                inbox_message = SolutionInboxMessage.get(data_dict['mk'])
                if redeem_lottery_winners(service_user, service_identity, app_user, user_profile.name, inbox_message):
                    title = common_translate(language, u'Success')
                    text = common_translate(language, u'loyalty-lottery-loot-receive')
                else:
                    title = common_translate(language, u'Error')
                    text = common_translate(language, u'Unfortunately you have not confirmed on time and lost your chance')
            else:
                language = self.request.get("language", DEFAULT_LANGUAGE)
                title = common_translate(language, u'Error')
                text = common_translate(language, u"error-occured-unknown-try-again")

        params = {
            'title': title,
            'text': text
        }

        jinja_template = JINJA_ENVIRONMENT.get_template('pages/loyalty_title_text.html')
        self.response.out.write(jinja_template.render(params))
