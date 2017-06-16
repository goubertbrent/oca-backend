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

import json
import logging

from google.appengine.ext import webapp, blobstore
from google.appengine.ext.webapp import blobstore_handlers

import cloudstorage
from mcfw.properties import azzert
from mcfw.rpc import parse_complex_value
from rogerthat.consts import ROGERTHAT_ATTACHMENTS_BUCKET
from rogerthat.to.registration import MobileInfoTO
from solutions.common.models.launcher import OSALauncherApp


class GetOSALaucherAppsHandler(webapp.RequestHandler):
    def post(self):
        app_id = self.request.POST.get("app_id", None)
        azzert(app_id is not None, "app_id is not found")
        azzert(app_id is not "com.mobicage.osa.launcher", "app_id is invalid")

        mobileInfo = self.request.POST.get("mobileInfo", None)
        logging.debug("GetOSALaucherAppsHandler mobileInfo: %s" % mobileInfo)
        azzert(mobileInfo is not None, "mobileInfo is not found")
        mobileInfoJSON = json.loads(mobileInfo)
        mobileInfo = parse_complex_value(MobileInfoTO, mobileInfoJSON, False)

        result = []

        for a in OSALauncherApp.all():
            result.append({"app_id": a.app_id, "version_code": a.version_code})

        r = json.dumps(dict(result=result))
        self.response.out.write(r)


class GetOSALaucherAppHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self):
        app_id = self.request.get("app_id", None)
        azzert(app_id is not None, "app_id is not found")
        logging.debug("GetOSALaucherAppHandler app_id: %s", app_id)

        app = OSALauncherApp.get_by_app_id(app_id)
        if app:
            try:
                filename = '%s/oca/launcher/apps/%s.apk' % (ROGERTHAT_ATTACHMENTS_BUCKET, app_id)
                cloudstorage.open(filename, 'r')
                blobstore_filename = '/gs' + filename
                blobstore_key = blobstore.create_gs_key(blobstore_filename)
            except cloudstorage.errors.NotFoundError:
                logging.warn("GetOSALaucherAppHandler NOT found in gcs")
                blobstore_key = app.package.key()

            self.send_blob(blobstore_key, content_type="application/vnd.android.package-archive",
                           save_as="%s-%s.apk" % (app.app_id, app.version_code))
        else:
            self.error(500)
