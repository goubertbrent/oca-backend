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

import os
from StringIO import StringIO

from google.appengine.ext import webapp, ndb
from google.appengine.ext.webapp import template

from mcfw.restapi import rest
from mcfw.rpc import returns, arguments
from rogerthat.rpc.models import ClientError


class MobileErrorHandler(webapp.RequestHandler):

    def get(self):
        cursor = self.request.get('cursor', None)
        start_cursor = ndb.Cursor.from_websafe_string(cursor) if cursor else None
        results, cursor, has_more = ClientError.list().fetch_page(50, start_cursor=start_cursor)
        path = os.path.join(os.path.dirname(__file__), 'client_error.html')

        self.response.out.write(template.render(path, {
            'errors': results,
            'cursor': cursor.to_websafe_string() if has_more else None
        }))


@rest('/mobiadmin/client_errors/<error_key:[^/]+>', 'get')
@returns(unicode)
@arguments(error_key=unicode)
def get_error_details(error_key):
    err = ClientError.create_key(error_key).get()
    s = StringIO()
    for prop_name, prop_value in sorted(err.to_dict().iteritems()):
        s.write(prop_name)
        s.write(': ')
        s.write(prop_value if isinstance(prop_value, basestring) else str(prop_value))
        s.write('\n\n')
    return s.getvalue()
