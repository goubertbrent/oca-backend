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
import os
import urllib

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template


class ServiceTools(webapp.RequestHandler):
    URL = "/admin/services?"
    ARGS = (("result", ""),)

    def redirect(self, **kwargs):
        params = [(k.encode('utf8'), v.encode('utf8')) for k, v in kwargs.items()]
        logging.info(params)
        return super(ServiceTools, self).redirect(str("/admin/services?") + urllib.urlencode(params, False))

    def get(self):
        context = dict(((key, self.request.get(key, default)) for key, default in self.ARGS))
        path = os.path.join(os.path.dirname(__file__), 'services.html')
        self.response.out.write(template.render(path, context))
