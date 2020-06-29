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


from google.appengine.ext import ndb
from google.appengine.ext.deferred.deferred import TaskHandler
import webapp2

from statistics.bizz import do_parse_all
from statistics.models.stats import StatsExportDaily


class MainHandler(webapp2.RequestHandler):

    def get(self):
        self.response.write('service-statistics main')


class ParseHandler(webapp2.RequestHandler):

    def get(self):
        do_parse_all()
        self.response.write('service-statistics parse')
        

class NukeHandler(webapp2.RequestHandler):

    def get(self):
        ndb.delete_multi(StatsExportDaily.query().fetch(keys_only=True))
        self.response.write('service-statistics nuke')



app = webapp2.WSGIApplication([
    ('/_ah/queue/deferred', TaskHandler),
    ('/', MainHandler),
    ('/parse', ParseHandler),
    ('/nuke', NukeHandler),
], debug=True)