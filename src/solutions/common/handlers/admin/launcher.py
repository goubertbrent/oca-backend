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

import os

from rogerthat.rpc import users
from rogerthat.utils import now
from google.appengine.ext import webapp, blobstore
from google.appengine.ext.webapp import template, blobstore_handlers
from solutions.common.models.launcher import OSALauncherApp


class OSAAppsPage(webapp.RequestHandler):

    def get(self):
        app = None
        app_id = self.request.get('id')
        new_app = self.request.get('new_app')
        if app_id:
            app = OSALauncherApp.get_by_app_id(app_id)

        if app or new_app:
            path = os.path.join(os.path.dirname(__file__), 'launcher_app.html')
            d = {'upload_url':blobstore.create_upload_url('/admin/osa/launcher/app/post')}
            if app:
                d['app'] = app
            else:
                d['new_app'] = 1
            self.response.out.write(template.render(path, d))
        else:
            path = os.path.join(os.path.dirname(__file__), 'launcher_apps.html')
            self.response.out.write(template.render(path, {
                'apps':(a for a in OSALauncherApp.all().order("-timestamp"))}))

class PostOSAAppHandler(blobstore_handlers.BlobstoreUploadHandler):

    def post(self):
        user = users.get_current_user()
        app_id = self.request.get("app_id")
        if not app_id:
            app_id = self.request.POST.get("app_id_hidden", None)

        if app_id:
            version_code = long(self.request.get("version_code"))
            app = OSALauncherApp.get_by_app_id(app_id)
            if not app:
                app = OSALauncherApp(key=OSALauncherApp.create_key(app_id))
            app.user = user
            app.timestamp = now()
            app.app_id = app_id
            app.version_code = version_code
            app.package = self.get_uploads("package")[0]
            app.put()

        self.redirect('/admin/osa/launcher/apps')
