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

from cgi import FieldStorage
import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from rogerthat.bizz.gcs import upload_to_gcs
from rogerthat.consts import ROGERTHAT_ATTACHMENTS_BUCKET
from rogerthat.rpc import users
from rogerthat.utils import now
from solutions.common.models.launcher import OSALauncherApp
import webapp2


class OSAAppsPage(webapp.RequestHandler):

    def get(self):
        app = None
        app_id = self.request.get('id')
        new_app = self.request.get('new_app')
        if app_id:
            app = OSALauncherApp.get_by_app_id(app_id)

        if app or new_app:
            path = os.path.join(os.path.dirname(__file__), 'launcher_app.html')
            d = {}
            if app:
                d['app'] = app
            else:
                d['new_app'] = 1
            self.response.out.write(template.render(path, d))
        else:
            path = os.path.join(os.path.dirname(__file__), 'launcher_apps.html')
            self.response.out.write(template.render(path, {
                'apps':(a for a in OSALauncherApp.all().order("-timestamp"))}))

class PostOSAAppHandler(webapp2.RequestHandler):

    def post(self):
        user = users.get_current_user()
        app_id = self.request.get("app_id")
        if not app_id:
            app_id = self.request.POST.get("app_id_hidden", None)

        if not app_id:
            self.redirect('/admin/osa/launcher/apps')
            return

        uploaded_file = self.request.POST.get('package')  # type: FieldStorage
        if not isinstance(uploaded_file, FieldStorage):
            self.redirect('/admin/osa/launcher/apps')
            return

        filename = '%s/oca/launcher/apps/%s.apk' % (ROGERTHAT_ATTACHMENTS_BUCKET, app_id)
        upload_to_gcs(uploaded_file.file, uploaded_file.type, filename)

        version_code = long(self.request.get("version_code"))
        app = OSALauncherApp.get_by_app_id(app_id)
        if not app:
            app = OSALauncherApp(key=OSALauncherApp.create_key(app_id))
        app.user = user
        app.timestamp = now()
        app.app_id = app_id
        app.version_code = version_code
        app.package = None
        app.put()

        self.redirect('/admin/osa/launcher/apps')
