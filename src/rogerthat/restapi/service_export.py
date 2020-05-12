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

import datetime
import json

from babel.dates import format_datetime
from google.appengine.ext.deferred import deferred

from rogerthat.bizz.gcs import get_serving_url
from rogerthat.bizz.import_export import export_service_data, import_service_data, validate_export_service_data
from rogerthat.consts import EXPORTS_BUCKET
from rogerthat.models import ServiceIdentity
from rogerthat.rpc import users
import webapp2 as webapp2


class ExportServiceDataHandler(webapp2.RequestHandler):
    def get(self):
        from rogerthat.bizz.service import ExportBrandingsException
        current_user = users.get_current_user()
        service_identity = self.request.GET.get('service_identity') or ServiceIdentity.DEFAULT
        date = format_datetime(datetime.datetime.now(), locale='en_GB', format='medium')
        result_path = '/%s/services/%s/%s/export %s.zip' % (EXPORTS_BUCKET, current_user.email(), service_identity, date)
        self.response.headers['Content-Type'] = 'application/json'
        try:
            validate_export_service_data(current_user, service_identity)
        except ExportBrandingsException as e:
            self.response.set_status(400)
            self.response.out.write(json.dumps({'message': e.message}))
            return
        deferred.defer(export_service_data, current_user, service_identity, result_path)
        self.response.out.write(json.dumps({'download_url': get_serving_url(result_path)}))


class ImportServiceDataHandler(webapp2.RequestHandler):
    def post(self):
        current_user = users.get_current_user()
        uploaded_file = self.request.POST.get('file', None)
        if uploaded_file is None:
            self.abort(400)
        if not uploaded_file.type.startswith('application/zip'):
            self.abort(400)
        file_content = uploaded_file.value
        import_service_data(current_user, file_content)
        self.redirect('/?sp=1')
